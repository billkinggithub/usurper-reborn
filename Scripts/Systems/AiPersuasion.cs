using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using UsurperRemake.Systems;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// What the model was allowed to change, after every limit has been applied. Everything here has
    /// already been checked against the list the game handed out; the caller can act on it without
    /// checking again.
    /// </summary>
    public sealed class PersuasionOutcome
    {
        /// <summary>The line the NPC says. One line, bounded.</summary>
        public string? Say { get; set; }

        /// <summary>An action from the offered list whose weight the model wants to move, or null.</summary>
        public string? NudgeAction { get; set; }

        /// <summary>How far to move it, already clamped to +/- <see cref="AiPersuasion.MaxNudge"/>.</summary>
        public double NudgeDelta { get; set; }

        /// <summary>A memory of an allowed type, or null when none was offered or accepted.</summary>
        public MemoryType? Memory { get; set; }

        public string? MemoryText { get; set; }

        public float MemoryImportance { get; set; }
        public float MemoryImpact { get; set; }

        /// <summary>True when a memory was offered but the daily allowance for this NPC was already
        /// spent. Surfaced so the screen can say so instead of silently showing nothing.</summary>
        public bool MemoryRefusedToday { get; set; }

        /// <summary>True when a memory was offered but not substantial enough: a type this may not create,
        /// or no text at all. Distinguished from an empty answer so the screen can say why nothing
        /// happened.</summary>
        public bool MemoryRefusedThin { get; set; }

        /// <summary>Why parts of the answer were thrown away, in the order they were checked.</summary>
        public List<string> Notes { get; } = new();

        /// <summary>Set when the answer could not be read at all.</summary>
        public string? Error { get; set; }

        public bool HasAnything => Say != null || NudgeAction != null || Memory != null;
    }

    /// <summary>
    /// v1.3.9: the one place where the model may influence a decision rather than only reword a line.
    ///
    /// The boundary is deliberate. It cannot set an affinity, add a goal, or touch the world tick: it may
    /// move the weight of one action it was shown, by a bounded amount, for the length of one
    /// conversation, and leave one ordinary memory of a type that words can plausibly create. Affinity
    /// then follows from that memory through the existing rule in MemorySystem, so there is no second
    /// path into the relationship numbers. Everything the engine calls a real event (an attack, a
    /// betrayal, a rescue) is out of reach.
    /// </summary>
    public static class AiPersuasion
    {
        /// <summary>Largest weight change a single conversation may make.</summary>
        public const double MaxNudge = 25;

        /// <summary>A memory the model writes is capped well below the importance of a real event, so it
        /// fades and can be outweighed by what actually happens.</summary>
        public const float MaxImportance = 0.35f;
        public const float MaxImpact = 0.30f;

        /// <summary>Marks a memory this layer wrote, so the daily allowance can find it and nothing
        /// else mistakes it for something the engine recorded.</summary>
        public const string MemoryTag = "ai_persuasion";

        public const int MaxSayChars = 200;
        public const int MaxMemoryChars = 120;

        /// <summary>
        /// Memories that are evidence this NPC actually did something for the player. Used to check a
        /// claim of past help instead of taking the player's word for it.
        /// </summary>
        public static readonly IReadOnlyList<MemoryType> ProofOfHelp = new[]
        {
            MemoryType.Helped,
            MemoryType.Defended,
            MemoryType.Saved,
            MemoryType.SharedItem,
            MemoryType.SharedDrink,
        };

        /// <summary>
        /// v1.3.9: whether this NPC remembers helping the player at all. Thanking someone for help they
        /// never gave is a lie, and the model cannot know that: it reads the sentence and believes it. The
        /// engine can know, because the help would be in the NPC's own memory, so a claim is checked
        /// against that. A promise of future help has no evidence either and earns nothing until it is
        /// kept, which is the same rule and the honest one.
        /// </summary>
        public static bool HasRealHelp(NPC npc, string playerName)
        {
            if (string.IsNullOrEmpty(playerName)) return false;
            var memories = npc?.Brain?.Memory?.GetMemoriesAboutCharacter(playerName);
            if (memories == null) return false;
            return memories.Any(m => ProofOfHelp.Contains(m.Type));
        }

        /// <summary>
        /// The only memory types a conversation may create. Each carries a fixed impression change in
        /// MemorySystem.ImpressionChangeFor, so this list is also the value limit.
        ///
        /// v1.3.9: Complimented and SocialInteraction are deliberately absent. Their changes, 0.2 and 0.3,
        /// are large next to how little they ask of the player, and a model asked to summarise any polite
        /// line reaches for them: "good to see you again" was earning the same as a promise of help, which
        /// made affection rise from small talk. What is left has to name something that happened between
        /// the two of them, or a threat. Attacked, Betrayed, Defeated, Saved, Defended, Abandoned and
        /// Murdered stay out: those are settled by what the engine did, never by what someone said.
        /// </summary>
        public static readonly IReadOnlyList<MemoryType> AllowedMemories = new[]
        {
            MemoryType.Helped,
            MemoryType.Traded,
            MemoryType.Insulted,
            MemoryType.Threatened,
        };

        /// <summary>Fit a model's text onto one line, within a length. Quotes around a spoken line are
        /// stripped; nothing else is "corrected", because the words are the model's job.</summary>
        public static string OneLine(string? text, int max)
        {
            if (string.IsNullOrWhiteSpace(text)) return "";
            string one = System.Text.RegularExpressions.Regex.Replace(text.Trim(), @"\s+", " ");
            one = one.Trim('"', '\u201c', '\u201d', '\u300c', '\u300d', ' ');
            if (max > 0 && one.Length > max) one = one[..max].TrimEnd();
            return one;
        }

        /// <summary>
        /// Read the model's answer against the rules. Pure: no network, no game state, so every limit can
        /// be checked without a terminal or a saved game.
        /// </summary>
        /// <param name="allowedActions">The action names the model was shown; anything else is dropped.
        /// </param>
        /// <param name="memoryAllowed">False once this NPC has already been moved by words today, which
        /// keeps a conversation from being repeated for a second helping.</param>
        public static PersuasionOutcome Parse(
            string? json, IReadOnlyList<string>? allowedActions, bool memoryAllowed)
        {
            var outcome = new PersuasionOutcome();

            // v1.3.9: an answer with no object at all is a failure worth logging, not an empty answer.
            // A real "{}" means the model decided nothing changed, and that is not an error.
            if (json == null || !json.Contains('{'))
            {
                outcome.Error = "no json";
                return outcome;
            }

            JsonDocument document;
            try
            {
                document = JsonDocument.Parse(ExtractObject(json));
            }
            catch (JsonException)
            {
                outcome.Error = "not json";
                return outcome;
            }

            using (document)
            {
                JsonElement root = document.RootElement;
                if (root.ValueKind != JsonValueKind.Object)
                {
                    outcome.Error = "not an object";
                    return outcome;
                }

                if (root.TryGetProperty("say", out var say) && say.ValueKind == JsonValueKind.String)
                {
                    string line = OneLine(say.GetString(), MaxSayChars);
                    if (line.Length > 0) outcome.Say = line;
                }

                ReadNudge(root, allowedActions, outcome);
                ReadMemory(root, memoryAllowed, outcome);
            }

            return outcome;
        }

        private static void ReadNudge(
            JsonElement root, IReadOnlyList<string>? allowedActions, PersuasionOutcome outcome)
        {
            if (!root.TryGetProperty("nudge", out var nudge) || nudge.ValueKind != JsonValueKind.Object)
                return;

            string wanted = nudge.TryGetProperty("action", out var action) && action.ValueKind == JsonValueKind.String
                ? action.GetString() ?? ""
                : "";
            double delta = nudge.TryGetProperty("delta", out var deltaElement)
                           && deltaElement.ValueKind == JsonValueKind.Number
                           && deltaElement.TryGetDouble(out double parsed)
                ? parsed
                : 0;

            if (wanted.Length == 0 || delta == 0) return;

            string? offered = allowedActions?.FirstOrDefault(
                a => string.Equals(a, wanted, StringComparison.OrdinalIgnoreCase));
            if (offered == null)
            {
                outcome.Notes.Add($"dropped nudge: '{OneLine(wanted, 40)}' is not one of the offered actions");
                return;
            }

            double clamped = Math.Clamp(delta, -MaxNudge, MaxNudge);
            if (clamped != delta) outcome.Notes.Add($"nudge clamped from {delta:0.#} to {clamped:0.#}");

            // v1.3.9: words may only dampen an impulse in this version. A trial had a character talk
            // about avenging a family and the model answered by raising "Find Better Weapons" from 80 to
            // 95, which would send him shopping instead of listening. Raising a drive is the direction
            // that changes what the world tick does, so it stays closed until there is evidence it is
            // wanted and a way to check it.
            if (clamped > 0)
            {
                outcome.Notes.Add($"dropped nudge: raising is not allowed ({clamped:0.#})");
                return;
            }

            outcome.NudgeAction = offered;
            outcome.NudgeDelta = clamped;
        }

        private static void ReadMemory(JsonElement root, bool memoryAllowed, PersuasionOutcome outcome)
        {
            if (!root.TryGetProperty("memory", out var memory) || memory.ValueKind != JsonValueKind.Object)
                return;

            if (!memoryAllowed)
            {
                outcome.MemoryRefusedToday = true;
                outcome.Notes.Add("dropped memory: already moved by words today");
                return;
            }

            string typeName = memory.TryGetProperty("type", out var type) && type.ValueKind == JsonValueKind.String
                ? type.GetString() ?? ""
                : "";
            string text = memory.TryGetProperty("text", out var textElement) && textElement.ValueKind == JsonValueKind.String
                ? OneLine(textElement.GetString(), MaxMemoryChars)
                : "";

            if (text.Length == 0)
            {
                outcome.MemoryRefusedThin = true;
                outcome.Notes.Add("dropped memory: no text");
                return;
            }

            MemoryType? allowed = AllowedMemories
                .Cast<MemoryType?>()
                .FirstOrDefault(t => Enum.TryParse<MemoryType>(typeName, ignoreCase: true, out var parsed)
                                     && parsed == t);
            if (allowed == null)
            {
                outcome.MemoryRefusedThin = true;
                outcome.Notes.Add($"dropped memory: type '{OneLine(typeName, 30)}' is not allowed from conversation");
                return;
            }

            float importance = memory.TryGetProperty("importance", out var imp) && imp.ValueKind == JsonValueKind.Number
                               && imp.TryGetSingle(out float importanceValue)
                ? importanceValue
                : 0.2f;
            float impact = memory.TryGetProperty("impact", out var hImpact) && hImpact.ValueKind == JsonValueKind.Number
                           && hImpact.TryGetSingle(out float impactValue)
                ? impactValue
                : 0f;

            importance = Math.Clamp(importance, 0f, MaxImportance);
            impact = Math.Clamp(impact, -MaxImpact, MaxImpact);

            outcome.Memory = allowed;
            outcome.MemoryText = text;
            outcome.MemoryImportance = importance;
            outcome.MemoryImpact = impact;
        }

        /// <summary>The model sometimes wraps its answer in prose or a fence; take the outermost object.</summary>
        public static string ExtractObject(string? content)
        {
            if (string.IsNullOrWhiteSpace(content)) return "{}";
            int start = content.IndexOf('{');
            int end = content.LastIndexOf('}');
            return start >= 0 && end > start ? content[start..(end + 1)] : "{}";
        }

        private static readonly HttpClient Http = new() { Timeout = Timeout.InfiniteTimeSpan };
        private const int TimeoutMs = 25000;

        /// <summary>
        /// Ask the model what, if anything, the player's words changed. Null when the mode is off, the
        /// call fails or the answer is unusable, so the conversation carries on exactly as before.
        /// </summary>
        public static async Task<PersuasionOutcome?> AskAsync(
            NPC npc,
            Character player,
            int relationLevel,
            IReadOnlyList<(string Action, double Weight)> candidates,
            string playerSaid,
            string languageName,
            bool memoryAllowed)
        {
            if (!AiSettings.IsActive || string.IsNullOrWhiteSpace(playerSaid)) return null;
            if (candidates == null || candidates.Count == 0) return null;
            if (BBS.DoorMode.IsInDoorMode || BBS.DoorMode.IsMudServerMode || BBS.DoorMode.IsMudRelayMode)
                return null;

            string offered = string.Join("\n", candidates.Select(c => $"- {c.Action} (weight {c.Weight:0.##})"));
            string allowedTypes = string.Join(", ", AllowedMemories);

            string system =
                "You are one character in a text adventure, in a conversation with the player. " +
                $"Write in {languageName}. Answer with JSON only, no prose, no code fence:\n" +
                "{\"say\":\"<your spoken line, one or two sentences>\", " +
                "\"nudge\":{\"action\":\"<one action from the list>\", \"delta\":<number>}, " +
                "\"memory\":{\"type\":\"<one allowed type>\", \"text\":\"<one short sentence>\", " +
                "\"importance\":<0 to 0.35>, \"impact\":<-0.3 to 0.3>}}\n" +
                "Omit nudge or memory entirely if nothing changed. " +
                $"nudge.delta must be between -{MaxNudge} and 0: your words can make you less inclined to " +
                "do something, never more. Raising a drive is refused. " +
                $"memory.type must be one of: {allowedTypes}. " +
                "Never invent events that did not happen. If the player thanks you for help you do not " +
                "remember giving, do not accept it as fact: answer with suspicion and record nothing.";

            string user =
                $"You are {npc?.Name2 ?? "someone"}" + (string.IsNullOrEmpty(npc?.Archetype) ? "" : $", a {npc!.Archetype}") + ".\n" +
                $"The player is {player?.Name2 ?? player?.Name1 ?? "a stranger"}, level {player?.Level}.\n" +
                $"You are {Standing(relationLevel)}.\n" +
                "The actions you are choosing between are:\n" + offered + "\n" +
                $"The player says to you:\n{playerSaid}";

            var payload = new
            {
                model = string.IsNullOrWhiteSpace(AiSettings.EffectiveModel) ? null : AiSettings.EffectiveModel,
                messages = new object[]
                {
                    new { role = "system", content = system },
                    new { role = "user", content = user },
                },
                max_tokens = 300,
                temperature = 0.7,
            };

            try
            {
                using var request = new HttpRequestMessage(HttpMethod.Post, AiSettings.Endpoint)
                {
                    Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"),
                };
                if (!string.IsNullOrWhiteSpace(AiSettings.ApiKey))
                    request.Headers.TryAddWithoutValidation("Authorization", "Bearer " + AiSettings.ApiKey);

                using var cts = new CancellationTokenSource(TimeoutMs);
                using var response = await Http.SendAsync(request, HttpCompletionOption.ResponseContentRead, cts.Token);
                if (!response.IsSuccessStatusCode)
                {
                    DebugLogger.Instance.LogWarning("AI", $"persuasion failed: HTTP {(int)response.StatusCode}");
                    return null;
                }

                string body = await response.Content.ReadAsStringAsync();
                using var doc = JsonDocument.Parse(body);
                string content = doc.RootElement.GetProperty("choices")[0]
                    .GetProperty("message").GetProperty("content").GetString() ?? "";

                var outcome = Parse(content, candidates.Select(c => c.Action).ToList(), memoryAllowed);
                if (outcome.Error != null)
                {
                    DebugLogger.Instance.LogWarning("AI", $"persuasion answer rejected: {outcome.Error}");
                    return null;
                }
                foreach (var note in outcome.Notes) DebugLogger.Instance.LogInfo("AI", $"persuasion {note}");
                return outcome.HasAnything ? outcome : null;
            }
            catch (Exception ex)
            {
                DebugLogger.Instance.LogWarning("AI", $"persuasion unavailable: {ex.GetType().Name}: {ex.Message}");
                return null;
            }
        }

        private static string Standing(int relationLevel) => relationLevel switch
        {
            >= 80 => "devoted to them",
            >= 50 => "fond of them",
            >= 20 => "civil towards them",
            >= -20 => "neutral towards them",
            >= -50 => "wary of them",
            _ => "hostile towards them",
        };
    }
}
