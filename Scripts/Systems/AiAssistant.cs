using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// v1.3.9: the assistant behind the two input prefixes.
    ///
    /// <c>/</c> means "this is what I do": the line is understood as one or more effects in the current
    /// situation, and the outcome is expressed as the menu key the game would have offered, plus
    /// narration and, when the player speaks, the exact words and tone for the NPC to receive.
    ///
    /// <c>@ai</c> means "this is for you": a question, a request for help, or a debug command to be
    /// proposed for confirmation.
    ///
    /// The model never executes anything. It answers with JSON that is validated here: a menu key is
    /// only accepted if the screen actually offers that key, text lengths are capped, and anything
    /// undecipherable is discarded. When the request is ambiguous the model answers with a question
    /// and the caller asks the player, which is why this returns a resolution rather than a string.
    /// </summary>
    public static class AiAssistant
    {
        private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(20) };
        private const int MaxNarration = 300;
        private const int MaxSay = 300;
        private const int MaxAnswer = 1200;

        /// <summary>One turn's outcome. Only one of these is usually set.</summary>
        public sealed class Resolution
        {
            public string? Ask { get; init; }
            public string? Choice { get; init; }
            public string? Narration { get; init; }
            public string? SayTarget { get; init; }
            public string? SayText { get; init; }
            public string? SayTone { get; init; }
            public string? Answer { get; init; }
            public string? Error { get; init; }

            public bool IsUsable => Ask != null || Choice != null || Narration != null
                                    || SayText != null || Answer != null;
        }

        /// <summary>True when the line is addressed to the assistant rather than acted out.</summary>
        public static bool IsAssistantLine(string raw) => raw.TrimStart().StartsWith("@ai", StringComparison.OrdinalIgnoreCase);

        /// <summary>True when the line is a free-form action.</summary>
        public static bool IsActionLine(string raw) => raw.TrimStart().StartsWith("/", StringComparison.Ordinal);

        /// <summary>Strip the prefix.</summary>
        public static string Strip(string raw)
        {
            var t = raw.Trim();
            if (IsAssistantLine(t)) return t[3..].Trim();
            if (IsActionLine(t)) return t[1..].Trim();
            return t;
        }

        /// <summary>
        /// Understands one line in the situation the screen shows. <paramref name="screen"/> is the text
        /// the player is looking at, which is also the only source of legal menu keys.
        /// </summary>
        public static async Task<Resolution> ResolveAsync(
            string utterance, bool assistantMode, string screen, string language, string contextNote = "")
        {
            if (string.IsNullOrWhiteSpace(utterance))
                return new Resolution { Ask = null, Error = "empty" };

            var legalKeys = MenuKeys(screen);
            string languageName = Loc.GetLanguageName(language);

            string system = assistantMode
                ? "You are the player's assistant inside a text adventure. Answer their question briefly " +
                  $"and concretely, in {languageName}. If they ask you to change game state, do not claim " +
                  "to have done it: reply with a {\"debug\":\"<command>\"} object instead and let the game ask " +
                  "them to confirm. Reply with JSON only."
                : "You read one free-form action from a player of a text adventure and describe what it " +
                  "amounts to in the current situation. One line can do several things at once: pick up a " +
                  "weapon, speak to someone, and take a stance. Capture all of them. " +
                  $"Write narration and speech in {languageName}. Reply with JSON only.";

            string schema =
                "{\"ask\":\"a question back, only when you genuinely cannot tell what they mean\"," +
                "\"choice\":\"ONE menu key visible on screen, or null\"," +
                "\"narration\":\"a short third-person description of what the player did\"," +
                "\"say\":{\"target\":\"who it is said to\",\"text\":\"their exact words\",\"tone\":\"threat|warm|formal|pleading|joking|cold\"}," +
                "\"answer\":\"only for @ai questions\"}";

            string user =
                $"The screen the player sees (the menu keys that are legal are the ones listed here):\n" +
                $"-----\n{Trim(screen, 3000)}\n-----\n\n" +
                (string.IsNullOrEmpty(contextNote) ? "" : $"Context: {contextNote}\n\n") +
                $"The player typed:\n{utterance}\n\n" +
                $"Reply with exactly one JSON object of this shape, with no other text:\n{schema}\n" +
                $"\"choice\" must be one of these keys or null: {string.Join(", ", legalKeys)}";

            var payload = new
            {
                model = string.IsNullOrWhiteSpace(AiSettings.Model) ? null : AiSettings.Model,
                messages = new object[]
                {
                    new { role = "system", content = system },
                    new { role = "user", content = user },
                },
                max_tokens = 500,
                temperature = 0.3,
            };

            using var request = new HttpRequestMessage(HttpMethod.Post, AiSettings.Endpoint)
            {
                Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"),
            };
            if (!string.IsNullOrWhiteSpace(AiSettings.ApiKey))
                request.Headers.TryAddWithoutValidation("Authorization", "Bearer " + AiSettings.ApiKey);

            using var response = await Http.SendAsync(request, HttpCompletionOption.ResponseContentRead);
            if (!response.IsSuccessStatusCode)
                return new Resolution { Error = $"http {(int)response.StatusCode}" };

            string body = await response.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(body);
            var choices = doc.RootElement.GetProperty("choices");
            if (choices.GetArrayLength() == 0) return new Resolution { Error = "no choices" };
            string? content = choices[0].GetProperty("message").GetProperty("content").GetString();
            return ParseResolution(content, legalKeys);
        }

        /// <summary>Validate the model's object. A menu key that the screen does not offer is dropped.</summary>
        public static Resolution ParseResolution(string? content, IReadOnlyCollection<string> legalKeys)
        {
            if (string.IsNullOrWhiteSpace(content)) return new Resolution { Error = "empty answer" };

            string json = ExtractJsonObject(content);
            if (json == null) return new Resolution { Error = "not json" };

            try
            {
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;

                string? ReadString(string name)
                {
                    if (!root.TryGetProperty(name, out var e) || e.ValueKind != JsonValueKind.String) return null;
                    var v = e.GetString()?.Trim();
                    return string.IsNullOrEmpty(v) ? null : v;
                }

                string? choice = ReadString("choice");
                if (choice != null)
                {
                    // the key must be one the screen actually offers: this is the whitelist that no
                    // amount of prompt wording can be trusted to enforce on its own
                    string? legal = legalKeys.FirstOrDefault(k => string.Equals(k, choice, StringComparison.OrdinalIgnoreCase));
                    choice = legal;
                }

                string? sayText = null, sayTarget = null, sayTone = null;
                if (root.TryGetProperty("say", out var say) && say.ValueKind == JsonValueKind.Object)
                {
                    sayText = say.TryGetProperty("text", out var t) && t.ValueKind == JsonValueKind.String
                        ? Cap(t.GetString(), MaxSay) : null;
                    sayTarget = say.TryGetProperty("target", out var g) && g.ValueKind == JsonValueKind.String
                        ? Cap(g.GetString(), 60) : null;
                    sayTone = say.TryGetProperty("tone", out var o) && o.ValueKind == JsonValueKind.String
                        ? Cap(o.GetString(), 20) : null;
                }

                return new Resolution
                {
                    Ask = Cap(ReadString("ask"), 300),
                    Choice = choice,
                    Narration = Cap(ReadString("narration"), MaxNarration),
                    SayText = string.IsNullOrWhiteSpace(sayText) ? null : sayText,
                    SayTarget = sayTarget,
                    SayTone = sayTone,
                    Answer = Cap(ReadString("answer"), MaxAnswer),
                };
            }
            catch (JsonException)
            {
                return new Resolution { Error = "bad json" };
            }
        }

        /// <summary>Find the menu keys offered by the screen text, e.g. " 3. Buy a sword".</summary>
        public static List<string> MenuKeys(string? screen)
        {
            var keys = new List<string>();
            if (string.IsNullOrEmpty(screen)) return keys;
            foreach (Match m in Regex.Matches(screen, @"(?m)^\s{0,4}([A-Za-z0-9])\.\s"))
            {
                string k = m.Groups[1].Value.ToUpperInvariant();
                if (!keys.Contains(k)) keys.Add(k);
            }
            return keys;
        }

        /// <summary>The model sometimes wraps JSON in prose or a code fence; take the outermost object.</summary>
        public static string? ExtractJsonObject(string text)
        {
            int start = text.IndexOf('{');
            int end = text.LastIndexOf('}');
            if (start < 0 || end <= start) return null;
            return text[start..(end + 1)];
        }

        private static string? Cap(string? s, int max)
        {
            if (string.IsNullOrWhiteSpace(s)) return null;
            s = s.Trim();
            return s.Length <= max ? s : s[..max];
        }

        private static string Trim(string s, int max) => s.Length <= max ? s : s[^max..];
    }
}
