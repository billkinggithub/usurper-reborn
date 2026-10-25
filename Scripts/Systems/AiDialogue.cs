using System;
using System.Collections.Concurrent;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// v1.3.9: the optional single-player AI dialogue layer.
    ///
    /// It never decides anything. The game has already chosen what this NPC is going to say, from the
    /// authored pools, weighted by personality, relationship and memory; this only asks a model to say
    /// the same thing in that NPC's own voice. If the call is off, slow, unreachable, misconfigured or
    /// returns something unusable, the authored line is shown and play continues without a hiccup.
    ///
    /// Nothing about the player is sent. Their name is replaced with a placeholder before the request
    /// and put back afterwards, so what leaves the machine is the NPC's character and the line, not who
    /// is playing.
    /// </summary>
    public static class AiDialogue
    {
        private const string PlayerPlaceholder = "{player}";
        // v1.3.9: one shared timeout meant either a slow greeting or a chat that always gave up. A
        // greeting is a rewrite that must not stall the walk-up, so it stays short; a reply to what the
        // player typed is awaited deliberately and gets a real budget.
        private const int GreetingTimeoutMs = 8000;
        private const int ChatTimeoutMs = 25000;
        private const int MaxCachedLines = 500;
        private const int MaxLineLength = 400;

        private static readonly HttpClient Http = new() { Timeout = Timeout.InfiniteTimeSpan };

        /// <summary>Re-voiced lines already received, keyed by NPC, language and the authored line.
        /// A hit costs nothing and keeps the same NPC saying the same thing the same way.</summary>
        private static readonly ConcurrentDictionary<string, string> Cache = new();
        private static int _failuresLogged;

        /// <summary>
        /// Returns the line to show: the model's re-voicing when the mode is on and everything worked,
        /// otherwise the authored line unchanged. Never throws and never blocks longer than the
        /// request timeout.
        /// </summary>
        public static string Rewrite(NPC npc, Player player, string authored)
        {
            if (string.IsNullOrWhiteSpace(authored)) return authored;
            if (!AiSettings.IsActive) return authored;
            if (!IsSinglePlayer()) return authored;

            string language = GameConfig.Language ?? "en";
            string playerName = player?.Name2 ?? player?.Name1 ?? "";
            string key = CacheKey(npc, language, authored);

            if (Cache.TryGetValue(key, out var cached))
                return Restore(cached, playerName);

            try
            {
                string? rewritten = RequestAsync(npc, authored, language, playerName, player)
                    .GetAwaiter().GetResult();
                rewritten = Tidy(rewritten);
                if (rewritten.Length == 0) return authored;

                if (Cache.Count >= MaxCachedLines) Cache.Clear();
                Cache[key] = rewritten;
                return Restore(rewritten, playerName);
            }
            catch (Exception ex)
            {
                // one line per session, not one per failed greeting
                if (Interlocked.Increment(ref _failuresLogged) == 1)
                    DebugLogger.Instance.LogWarning("AI",
                        $"AI dialogue unavailable, using authored lines: {ex.GetType().Name}: {ex.Message}");
                return authored;
            }
        }

        /// <summary>
        /// v1.3.9: one exchange inside an already-open conversation. The player typed what they want to
        /// say; this returns what the NPC says back, in their own voice, reacting to the words and to how
        /// they feel about the player. Null when the mode is off or the call fails, so the conversation
        /// simply carries on with the menu.
        /// </summary>
        public static string? ChatReply(NPC npc, string playerSaid, int relationLevel, string languageName)
        {
            if (!AiSettings.IsActive || string.IsNullOrWhiteSpace(playerSaid)) return null;
            if (!IsSinglePlayer()) return null;

            try
            {
                string? reply = ChatReplyAsync(npc, playerSaid, relationLevel, languageName)
                    .GetAwaiter().GetResult();
                reply = Tidy(reply);
                if (reply.Length == 0)
                {
                    DebugLogger.Instance.LogWarning("AI", "chat reply was empty after tidying");
                    return null;
                }
                return reply;
            }
            catch (Exception ex)
            {
                if (Interlocked.Increment(ref _failuresLogged) == 1)
                    DebugLogger.Instance.LogWarning("AI", $"chat reply unavailable: {ex.GetType().Name}: {ex.Message}");
                return null;
            }
        }

        private static async Task<string?> ChatReplyAsync(NPC npc, string playerSaid, int relationLevel, string languageName)
        {
            var p = npc?.Personality;
            string standing = relationLevel switch
            {
                >= 80 => "devoted to them",
                >= 50 => "fond of them",
                >= 20 => "civil towards them",
                >= -20 => "neutral towards them",
                >= -50 => "wary of them",
                _ => "hostile towards them",
            };

            string system =
                "You are role playing one character in a text adventure. Answer the player in that " +
                "character's own voice, reacting to what was just said to you. " +
                $"Write in {languageName}. Reply with the spoken line alone: no quotes, no stage " +
                $"directions, one or two sentences, at most {MaxLineLength} characters.";

            string user =
                $"You are {npc?.Name2 ?? "someone"}" + (string.IsNullOrEmpty(npc?.Archetype) ? "" : $", a {npc!.Archetype}") + ".\n" +
                (p == null ? "" :
                    $"Your nature: aggressive {p.Aggression:0.0}, loyal {p.Loyalty:0.0}, clever {p.Intelligence:0.0}, " +
                    $"sociable {p.Sociability:0.0}, cautious {p.Caution:0.0}, vengeful {p.Vengefulness:0.0}.\n") +
                $"You are {standing}.\n" +
                $"The player says to you:\n{playerSaid}";

            var payload = new
            {
                model = string.IsNullOrWhiteSpace(AiSettings.EffectiveModel) ? null : AiSettings.EffectiveModel,
                messages = new object[]
                {
                    new { role = "system", content = system },
                    new { role = "user", content = user },
                },
                max_tokens = 150,
                temperature = 0.8,
            };

            using var request = new HttpRequestMessage(HttpMethod.Post, AiSettings.Endpoint)
            {
                Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"),
            };
            if (!string.IsNullOrWhiteSpace(AiSettings.ApiKey))
                request.Headers.TryAddWithoutValidation("Authorization", "Bearer " + AiSettings.ApiKey);

            using var cts = new CancellationTokenSource(ChatTimeoutMs);
            using var response = await Http.SendAsync(request, HttpCompletionOption.ResponseContentRead, cts.Token);
            if (!response.IsSuccessStatusCode)
            {
                string detail = "";
                try
                {
                    string errorBody = await response.Content.ReadAsStringAsync();
                    using var errorDoc = JsonDocument.Parse(errorBody);
                    if (errorDoc.RootElement.TryGetProperty("error", out var err)
                        && err.TryGetProperty("message", out var msg))
                        detail = msg.GetString() ?? "";
                }
                catch { }
                DebugLogger.Instance.LogWarning("AI",
                    $"chat reply failed: HTTP {(int)response.StatusCode}" + (detail.Length > 0 ? $": {detail}" : ""));
                return null;
            }

            string body = await response.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(body);
            var choices = doc.RootElement.GetProperty("choices");
            if (choices.GetArrayLength() == 0) return null;
            return choices[0].GetProperty("message").GetProperty("content").GetString();
        }

        /// <summary>The model is only for solo play for now; a door session, a MUD client or an online
        /// save must never depend on a request going out.</summary>
        private static bool IsSinglePlayer()
            => !BBS.DoorMode.IsInDoorMode && !BBS.DoorMode.IsMudServerMode && !BBS.DoorMode.IsMudRelayMode;

        private static string CacheKey(NPC npc, string language, string authored)
            => $"{npc?.Name2 ?? npc?.Name1}|{language}|{authored}";

        private static string Restore(string text, string playerName)
            => string.IsNullOrEmpty(playerName) ? text : text.Replace(PlayerPlaceholder, playerName);

        /// <summary>
        /// v1.3.9: fit a model's answer onto one line instead of throwing it away. Rejecting anything that
        /// contained a newline discarded perfectly good answers over a formatting detail, and the player
        /// saw that as the character refusing to answer. Wrapping quotes are stripped for the same reason.
        /// </summary>
        private static string Tidy(string? text)
        {
            if (string.IsNullOrWhiteSpace(text)) return "";
            string one = System.Text.RegularExpressions.Regex.Replace(text.Trim(), @"\s+", " ");
            one = one.Trim('"', '\u201c', '\u201d', '\u300c', '\u300d', ' ');
            if (one.Length > MaxLineLength) one = one[..MaxLineLength].TrimEnd() + "...";
            return one;
        }

        private static async Task<string?> RequestAsync(
            NPC npc, string authored, string language, string playerName, Player? player)
        {
            var p = npc?.Personality;
            string traits = p == null ? "unremarkable" : string.Join(", ", new[]
            {
                Describe("aggressive", p.Aggression), Describe("greedy", p.Greed),
                Describe("brave", p.Courage), Describe("loyal", p.Loyalty),
                Describe("vengeful", p.Vengefulness), Describe("impulsive", p.Impulsiveness),
                Describe("sociable", p.Sociability), Describe("ambitious", p.Ambition),
                Describe("trustworthy", p.Trustworthiness), Describe("cautious", p.Caution),
                Describe("clever", p.Intelligence), Describe("mystical", p.Mysticism),
                Describe("patient", p.Patience), Describe("romantic", p.Romanticism),
            }.Where(s => s != null));

            string languageName = Loc.GetLanguageName(language);
            string system =
                "You rewrite one line of dialogue for a character in a text adventure. " +
                "Keep the meaning, the intent and any information in the original line exactly. " +
                "Change only the wording so it sounds like this particular character. " +
                $"Write in {languageName}. Reply with the line alone: no quotes, no explanation, one line, " +
                $"at most {MaxLineLength} characters, no markdown. " +
                $"If the line contains {PlayerPlaceholder}, keep that placeholder exactly where the name goes.";

            var subject = new StringBuilder();
            subject.Append($"Name: {MaskName(npc?.Name2 ?? npc?.Name1, playerName)}\n");
            if (!string.IsNullOrEmpty(npc?.Archetype)) subject.Append($"Trade: {npc.Archetype}\n");
            subject.Append($"Character traits: {traits}\n");
            if (npc != null) subject.Append($"Their feeling toward the listener: {RelationshipWord(npc, playerName)}\n");
            if (npc?.Memory != null)
            {
                var memories = npc.Memory.GetMemoriesAboutCharacter(playerName);
                if (memories.Count > 0)
                {
                    var strongest = memories[0];
                    subject.Append($"They remember: {StrongestMemory(memories)}\n");
                }
            }
            subject.Append($"\nLine to rewrite:\n{MaskName(authored, playerName)}");

            var payload = new
            {
                model = string.IsNullOrWhiteSpace(AiSettings.Model) ? null : AiSettings.Model,
                messages = new object[]
                {
                    new { role = "system", content = system },
                    new { role = "user", content = subject.ToString() },
                },
                max_tokens = 120,
                temperature = 0.8,
            };

            using var request = new HttpRequestMessage(HttpMethod.Post, AiSettings.Endpoint)
            {
                Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"),
            };
            if (!string.IsNullOrWhiteSpace(AiSettings.ApiKey))
                request.Headers.TryAddWithoutValidation("Authorization", "Bearer " + AiSettings.ApiKey);

            using var cts = new CancellationTokenSource(GreetingTimeoutMs);
            using var response = await Http.SendAsync(request, HttpCompletionOption.ResponseContentRead, cts.Token);
            if (!response.IsSuccessStatusCode) return null;

            string body = await response.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(body);
            var choices = doc.RootElement.GetProperty("choices");
            if (choices.GetArrayLength() == 0) return null;
            var content = choices[0].GetProperty("message").GetProperty("content").GetString();
            return content;
        }

        private static string MaskName(string? text, string playerName)
            => string.IsNullOrEmpty(text) || string.IsNullOrEmpty(playerName)
                ? text ?? ""
                : text.Replace(playerName, PlayerPlaceholder);

        private static string? Describe(string word, float value)
            => value > 0.7f ? word : null;

        private static string RelationshipWord(NPC npc, string playerName)
        {
            int level = npc?.Relationships?.GetRelationshipWith(playerName) ?? 0;
            return level switch
            {
                >= 80 => "devoted",
                >= 50 => "friendly",
                >= 20 => "civil",
                >= 0 => "neutral",
                >= -30 => "wary",
                _ => "hostile",
            };
        }

        private static string StrongestMemory(System.Collections.Generic.List<MemoryEvent> memories)
        {
            var m = memories[0];
            return m.Type switch
            {
                MemoryType.Saved => "the listener saved their life",
                MemoryType.Betrayed => "the listener betrayed them",
                MemoryType.Attacked => "the listener attacked them",
                MemoryType.Helped => "the listener helped them",
                MemoryType.Defended => "the listener defended them",
                MemoryType.Insulted => "the listener insulted them",
                MemoryType.Complimented => "the listener complimented them",
                MemoryType.Traded => "they have done business together",
                MemoryType.SharedDrink => "they shared a drink",
                MemoryType.SharedItem => "the listener gave them something",
                _ => "they have met before",
            };
        }
    }
}
