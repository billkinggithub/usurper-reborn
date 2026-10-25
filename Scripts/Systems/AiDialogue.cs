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
        private static readonly TimeSpan RequestTimeout = TimeSpan.FromMilliseconds(1500);
        private const int MaxCachedLines = 500;
        private const int MaxLineLength = 400;

        private static readonly HttpClient Http = new() { Timeout = RequestTimeout };

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
                if (string.IsNullOrWhiteSpace(rewritten)) return authored;

                rewritten = rewritten.Trim();
                if (!IsUsable(rewritten)) return authored;

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

        /// <summary>The model is only for solo play for now; a door session, a MUD client or an online
        /// save must never depend on a request going out.</summary>
        private static bool IsSinglePlayer()
            => !BBS.DoorMode.IsInDoorMode && !BBS.DoorMode.IsMudServerMode && !BBS.DoorMode.IsMudRelayMode;

        /// <summary>
        /// v1.3.9: the NPC's answer to something the player actually said, in this NPC's voice, reacting
        /// to both the words and the tone. Null when the mode is off or the call fails, in which case the
        /// conversation simply continues and the player's line stands on its own.
        /// </summary>
        public static string? ReplyTo(NPC npc, Player player, string playerSaid, string? tone)
        {
            if (!AiSettings.IsActive || !IsSinglePlayer()) return null;
            if (string.IsNullOrWhiteSpace(playerSaid)) return null;

            string language = GameConfig.Language ?? "en";
            string playerName = player?.Name2 ?? player?.Name1 ?? "";
            try
            {
                string reply = ReplyAsync(npc, playerSaid, tone, languageName: Loc.GetLanguageName(language))
                    .GetAwaiter().GetResult();
                if (string.IsNullOrWhiteSpace(reply)) return null;
                reply = reply.Trim();
                if (!IsUsable(reply)) return null;
                return MaskName(reply, playerName).Replace(PlayerPlaceholder, playerName);
            }
            catch (Exception ex)
            {
                if (Interlocked.Increment(ref _failuresLogged) == 1)
                    DebugLogger.Instance.LogWarning("AI", $"NPC reply unavailable: {ex.GetType().Name}: {ex.Message}");
                return null;
            }
        }

        private static async Task<string?> ReplyAsync(NPC npc, string playerSaid, string? tone, string languageName)
        {
            var p = npc?.Personality;
            string system =
                "You are role playing one character in a text adventure. Answer what the player just said " +
                "in that character's own voice, reacting to both the words and the manner. " +
                $"Write in {languageName}. Reply with the spoken line alone: no quotes, no stage directions, " +
                $"one line, at most {MaxLineLength} characters.";

            string user =
                $"Character: {npc?.Name2 ?? "someone"}" + (string.IsNullOrEmpty(npc?.Archetype) ? "" : $", a {npc!.Archetype}") + "\n" +
                (p == null ? "" :
                    $"Traits: aggressive {p.Aggression:0.0}, loyal {p.Loyalty:0.0}, clever {p.Intelligence:0.0}, " +
                    $"sociable {p.Sociability:0.0}, cautious {p.Caution:0.0}, vengeful {p.Vengefulness:0.0}\n") +
                $"They feel about the player: {RelationshipWord(npc, "")}\n" +
                $"The player said, in a {tone ?? "neutral"} manner:\n{playerSaid}";

            var payload = new
            {
                model = string.IsNullOrWhiteSpace(AiSettings.EffectiveModel) ? null : AiSettings.EffectiveModel,
                messages = new object[]
                {
                    new { role = "system", content = system },
                    new { role = "user", content = user },
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

            using var response = await Http.SendAsync(request, HttpCompletionOption.ResponseContentRead);
            if (!response.IsSuccessStatusCode) return null;
            string body = await response.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(body);
            var choices = doc.RootElement.GetProperty("choices");
            if (choices.GetArrayLength() == 0) return null;
            return choices[0].GetProperty("message").GetProperty("content").GetString();
        }

        private static string CacheKey(NPC npc, string language, string authored)
            => $"{npc?.Name2 ?? npc?.Name1}|{language}|{authored}";

        private static string Restore(string text, string playerName)
            => string.IsNullOrEmpty(playerName) ? text : text.Replace(PlayerPlaceholder, playerName);

        private static bool IsUsable(string text)
            => text.Length > 0 && text.Length <= MaxLineLength && !text.Contains('\n') && !text.Contains('\r');

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
                model = string.IsNullOrWhiteSpace(AiSettings.EffectiveModel) ? null : AiSettings.EffectiveModel,
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

            using var response = await Http.SendAsync(request, HttpCompletionOption.ResponseContentRead);
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
