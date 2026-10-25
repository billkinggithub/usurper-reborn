using System;
using System.IO;
using System.Text.Json;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// v1.3.9: the few choices that belong to the player rather than to a character, kept beside the AI
    /// settings. Today that is the language, because it was being asked for again on every launch: the
    /// main menu starts in English, and the saved language only reached it once a character was loaded.
    ///
    /// The file lives where this process can write, which is not always the user data folder, so it goes
    /// through the same probe the settings do.
    /// </summary>
    public static class UserSettings
    {
        private const string FileName = "settings.json";

        public static string Language { get; set; } = "";

        public static string FilePath => Path.Combine(UserDataPaths.Writable(), FileName);

        public static void Load()
        {
            try
            {
                if (!File.Exists(FilePath)) return;
                using var document = JsonDocument.Parse(File.ReadAllText(FilePath));
                if (document.RootElement.TryGetProperty("language", out var language)
                    && language.ValueKind == JsonValueKind.String)
                {
                    string code = language.GetString() ?? "";
                    if (code.Length > 0) Language = code;
                }
                DebugLogger.Instance.LogInfo("SETTINGS", $"language={Language}");
            }
            catch (Exception ex)
            {
                DebugLogger.Instance.LogWarning("SETTINGS", $"could not read {FilePath}: {ex.Message}");
            }
        }

        public static void Save()
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(FilePath)!);
                var payload = new { language = Language };
                File.WriteAllText(FilePath, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
            }
            catch (Exception ex)
            {
                DebugLogger.Instance.LogWarning("SETTINGS", $"could not write {FilePath}: {ex.Message}");
            }
        }

        /// <summary>Record the language the player just picked, so the next launch opens in it.</summary>
        public static void RememberLanguage(string? code)
        {
            if (string.IsNullOrWhiteSpace(code)) return;
            if (string.Equals(Language, code, StringComparison.Ordinal)) return;
            Language = code;
            Save();
        }
    }
}
