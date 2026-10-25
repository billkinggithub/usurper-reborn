using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// v1.3.9: the optional AI mode for NPC dialogue.
    ///
    /// Off by default and never required. When it is on, NPC lines may be written by a language model
    /// instead of picked from the authored pools; when it is off, or the endpoint or key is missing,
    /// every line comes from the authored pools exactly as before. The player can switch between the
    /// two at any time from the preferences screen, and the switch takes effect on the next line.
    ///
    /// The credentials live in their own file next to the saves rather than inside a save, so they are
    /// not copied into every character and are not carried around with a save file. An environment
    /// variable wins over the file, which lets a server operator keep the key out of the filesystem.
    /// </summary>
    public static class AiSettings
    {
        private const string FileName = "ai.json";

        /// <summary>The runtime switch. Not the same as <see cref="IsActive"/>: this may be on while
        /// the endpoint or key is still missing.</summary>
        public static bool Enabled { get; set; }

        /// <summary>OpenAI-compatible chat-completions URL. A local Ollama endpoint also works
        /// (http://localhost:11434/v1/chat/completions) and needs no key.</summary>
        public static string Endpoint { get; set; } = "";

        /// <summary>Bearer token. Never logged, never shown in full on screen.</summary>
        public static string ApiKey { get; set; } = "";

        /// <summary>Model identifier. Empty means the endpoint's default.</summary>
        public static string Model { get; set; } = "";

        /// <summary>True when the mode is on and there is somewhere to send the request.</summary>
        public static bool IsActive => Enabled && !string.IsNullOrWhiteSpace(Endpoint);

        /// <summary>True when the player has filled in enough to be worth trying.</summary>
        public static bool IsConfigured => !string.IsNullOrWhiteSpace(Endpoint);

        /// <summary>
        /// v1.3.9: the model to send. Most OpenAI-compatible services require one, and the address
        /// already says which service this is, so a known provider fills the gap instead of making the
        /// player look the name up. An explicit value always wins, and USURPER_LLM_MODEL overrides both.
        /// </summary>
        public static string EffectiveModel
        {
            get
            {
                if (!string.IsNullOrWhiteSpace(Model)) return Model.Trim();
                string e = Endpoint ?? "";
                // Providers rename their models (DeepSeek's are flash and pro now, not what they were
                // last year), so the only safe default is one the player typed. For a local server the
                // name is ours to pick.
                if (e.Contains("11434", StringComparison.Ordinal) || e.Contains("localhost", StringComparison.OrdinalIgnoreCase))
                    return "llama3.1";
                if (e.Contains("openai.com", StringComparison.OrdinalIgnoreCase)) return "gpt-4o-mini";
                return "";   // unknown provider: ask the player rather than guess a stale name
            }
        }

        public static string FilePath => Path.Combine(UserDataPaths.Writable(), FileName);

        /// <summary>What the preferences screen shows next to the toggle.</summary>
        public static string DescribeState()
        {
            if (!Enabled) return "off";
            if (!IsConfigured) return "on, no address set";
            return string.IsNullOrEmpty(ApiKey) ? "on, no key set" : "on";
        }

        /// <summary>The key as it may be shown on screen: enough to recognise, not enough to use.</summary>
        public static string MaskedKey()
        {
            if (string.IsNullOrEmpty(ApiKey)) return "";
            if (ApiKey.Length <= 8) return new string('*', ApiKey.Length);
            return ApiKey[..4] + new string('*', Math.Min(12, ApiKey.Length - 8)) + ApiKey[^4..];
        }

        private sealed class Stored
        {
            [JsonPropertyName("enabled")] public bool Enabled { get; set; }
            [JsonPropertyName("endpoint")] public string? Endpoint { get; set; }
            [JsonPropertyName("apiKey")] public string? ApiKey { get; set; }
            [JsonPropertyName("model")] public string? Model { get; set; }
        }

        /// <summary>Trim what a paste usually brings with it. A key with a trailing newline becomes an
        /// invalid HTTP header, and a padded endpoint stops matching the provider's route.</summary>
        private static void Normalize()
        {
            Endpoint = (Endpoint ?? "").Trim();
            ApiKey = (ApiKey ?? "").Trim();
            Model = (Model ?? "").Trim();
        }

        /// <summary>Read the file, then let the environment override it. A missing or broken file is
        /// not an error: the mode simply stays off.</summary>
        public static void Load()
        {
            try
            {
                if (File.Exists(FilePath))
                {
                    var stored = JsonSerializer.Deserialize<Stored>(File.ReadAllText(FilePath));
                    if (stored != null)
                    {
                        Enabled = stored.Enabled;
                        Endpoint = stored.Endpoint ?? "";
                        ApiKey = stored.ApiKey ?? "";
                        Model = stored.Model ?? "";
                    }
                }
            }
            catch (Exception ex)
            {
                DebugLogger.Instance.LogWarning("AI", $"Could not read {FilePath}: {ex.Message}");
                Enabled = false;
            }

            var envEndpoint = Environment.GetEnvironmentVariable("USURPER_LLM_ENDPOINT");
            var envKey = Environment.GetEnvironmentVariable("USURPER_LLM_API_KEY");
            var envModel = Environment.GetEnvironmentVariable("USURPER_LLM_MODEL");
            if (!string.IsNullOrWhiteSpace(envEndpoint)) Endpoint = envEndpoint;
            if (!string.IsNullOrWhiteSpace(envKey)) ApiKey = envKey;
            if (!string.IsNullOrWhiteSpace(envModel)) Model = envModel;

            Normalize();

            // v1.3.9: say what was found, never the values themselves. Without this, "it asks me again
            // every time" cannot be told apart from a file that was simply never loaded.
            DebugLogger.Instance.LogInfo("AI",
                $"settings: enabled={Enabled}, endpoint={(string.IsNullOrEmpty(Endpoint) ? "none" : "set")}, " +
                $"key={(string.IsNullOrEmpty(ApiKey) ? "none" : "set")}, " +
                $"model={(string.IsNullOrEmpty(Model) ? "default" : Model)}");
        }

        /// <summary>What an edit did, so the screen can say so.</summary>
        public enum EditOutcome { Unchanged, Cleared, Stored }

        /// <summary>
        /// v1.3.9: apply one edited text setting. An empty line keeps what is already stored, because a
        /// player who opens the prompt and presses Enter means "never mind", not "delete it"; a single
        /// dash clears it on purpose. This is the rule that made the address and key have to be typed
        /// again on every visit, so it is a pure function that can be tested on its own.
        /// </summary>
        public static (string Value, EditOutcome Outcome) ApplyEdit(string current, string? entered)
        {
            string value = (entered ?? "").Trim();
            if (value.Length == 0) return (current ?? "", EditOutcome.Unchanged);
            if (value == "-") return ("", EditOutcome.Cleared);
            return (value, EditOutcome.Stored);
        }

        /// <summary>Write the current values back. Failing to write is logged and ignored: the mode
        /// still works for this session.</summary>
        public static void Save()
        {
            try
            {
                Normalize();
                Directory.CreateDirectory(UserDataPaths.Get());
                var stored = new Stored { Enabled = Enabled, Endpoint = Endpoint, ApiKey = ApiKey, Model = Model };
                File.WriteAllText(FilePath, JsonSerializer.Serialize(stored,
                    new JsonSerializerOptions { WriteIndented = true }));
            }
            catch (Exception ex)
            {
                DebugLogger.Instance.LogWarning("AI", $"Could not write {FilePath}: {ex.Message}");
            }
        }
    }
}
