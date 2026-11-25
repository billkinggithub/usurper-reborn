using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace UsurperRemake.SaveEditor;

/// <summary>
/// A local editor for single-player saves, served to the browser so a field is a form control instead of a
/// prompt in a console.
///
/// It is deliberately narrow. It edits the scalar fields of the player object and nothing else: no NPCs, no
/// world state, no schema guessing. Only keys that already exist are accepted, a value must keep the type it
/// already had, and every write keeps a timestamped copy of the file it replaced, so a bad edit is one file
/// away from undone.
///
/// The game must be closed while this runs. It holds its own save open and writes over it on autosave, so an
/// edit made while playing is lost or fought over.
/// </summary>
public static class Program
{
    private const string GameProject = "usurper-reloaded.csproj";

    public static void Main(string[] args)
    {
        string? savesOverride = null;
        for (int i = 0; i < args.Length; i++)
            if (args[i] == "--saves" && i + 1 < args.Length) savesOverride = args[i + 1];

        string saves = savesOverride ?? FindSavesDirectory();
        if (!Directory.Exists(saves))
        {
            Console.Error.WriteLine($"No save folder at {saves}. Run the game once, or pass --saves <path>.");
            Environment.Exit(1);
        }

        var builder = WebApplication.CreateBuilder(args);
        builder.WebHost.UseUrls("http://127.0.0.1:5199");
        var app = builder.Build();

        app.UseDefaultFiles();
        app.UseStaticFiles();

        Console.WriteLine($"Saves: {saves}");
        Console.WriteLine("Open http://127.0.0.1:5199   (close the game before saving)");

        app.MapGet("/api/saves", () =>
        {
            var files = new DirectoryInfo(saves)
                .GetFiles("*.json")
                .OrderByDescending(f => f.LastWriteTime)
                .Select(f => new
                {
                    name = f.Name,
                    size = f.Length,
                    modified = f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture),
                });
            return Results.Json(files);
        });

        app.MapGet("/api/player", (string file) =>
        {
            string path = Resolve(saves, file);
            if (path == null) return Results.NotFound(new { error = "no such save" });

            JsonNode root = JsonNode.Parse(File.ReadAllText(path)) ?? new JsonObject();
            JsonObject? player = root["player"] as JsonObject;
            if (player == null) return Results.BadRequest(new { error = "this save has no player object" });

            var fields = player
                .Where(pair => IsScalar(pair.Value))
                .Select(pair => new
                {
                    key = pair.Key,
                    value = ScalarText(pair.Value),
                    kind = KindOf(pair.Value),
                })
                .OrderBy(f => f.key, StringComparer.Ordinal);

            return Results.Json(new
            {
                file,
                level = ScalarText(player["level"]),
                name = ScalarText(player["name2"]),
                fields,
            });
        });

        app.MapPost("/api/player", (SaveRequest request) =>
        {
            string path = Resolve(saves, request.File);
            if (path == null) return Results.NotFound(new { error = "no such save" });

            string originalText = File.ReadAllText(path);
            JsonNode? parsed = JsonNode.Parse(originalText);
            if (parsed?["player"] is not JsonObject player)
                return Results.BadRequest(new { error = "this save has no player object" });

            var applied = new List<string>();
            var refused = new List<string>();

            foreach (var (key, raw) in request.Values)
            {
                if (!player.TryGetPropertyValue(key, out JsonNode? current))
                {
                    refused.Add($"{key}: not a field this save has");
                    continue;
                }
                if (!IsScalar(current))
                {
                    refused.Add($"{key}: not a simple value");
                    continue;
                }
                if (!TryCoerce(current, raw, out JsonNode? updated, out string why))
                {
                    refused.Add($"{key}: {why}");
                    continue;
                }
                player[key] = updated;
                applied.Add($"{key} = {ScalarText(updated)}");
            }

            if (applied.Count == 0)
                return Results.Json(new { ok = false, applied, refused });

            string backup = $"{path}.bak-{DateTime.Now:yyyyMMdd-HHmmss}";
            File.Copy(path, backup, overwrite: false);

            string temporary = path + ".editing";
            File.WriteAllText(temporary, parsed!.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
            File.Move(temporary, path, overwrite: true);

            return Results.Json(new
            {
                ok = true,
                applied,
                refused,
                backup = Path.GetFileName(backup),
            });
        });

        app.Run();
    }

    public sealed record SaveRequest(string File, Dictionary<string, string> Values);

    /// <summary>Resolve a file name inside the saves folder, and refuse anything that leaves it.</summary>
    private static string? Resolve(string saves, string file)
    {
        if (string.IsNullOrWhiteSpace(file)) return null;
        string candidate = Path.GetFullPath(Path.Combine(saves, file));
        string root = Path.GetFullPath(saves);
        if (!candidate.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) return null;
        return File.Exists(candidate) ? candidate : null;
    }

    private static bool IsScalar(JsonNode? node)
        => node is JsonValue value
           && value.GetValueKind() is JsonValueKind.Number or JsonValueKind.String
               or JsonValueKind.True or JsonValueKind.False;

    private static string KindOf(JsonNode? node) => node?.GetValueKind() switch
    {
        JsonValueKind.Number => "number",
        JsonValueKind.String => "text",
        JsonValueKind.True or JsonValueKind.False => "bool",
        _ => "other",
    };

    private static string ScalarText(JsonNode? node)
    {
        if (node is not JsonValue value) return "";
        return value.GetValueKind() switch
        {
            JsonValueKind.String => value.GetValue<string>() ?? "",
            JsonValueKind.Number => value.ToJsonString(),
            JsonValueKind.True => "true",
            JsonValueKind.False => "false",
            _ => "",
        };
    }

    /// <summary>
    /// Turn the text from the browser into a value of the kind the field already had. A number stays a
    /// number and keeps its integral or fractional shape, so a level cannot arrive as "5.5" and a gold
    /// total cannot lose its digits to a float.
    /// </summary>
    private static bool TryCoerce(JsonNode? current, string raw, out JsonNode? updated, out string why)
    {
        updated = null;
        why = "";
        string text = (raw ?? "").Trim();

        switch (KindOf(current))
        {
            case "number":
                string existing = ScalarText(current);
                bool integral = !existing.Contains('.') && !existing.Contains('e', StringComparison.OrdinalIgnoreCase);

                if (integral)
                {
                    if (!long.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out long asLong))
                    {
                        why = "needs a whole number";
                        return false;
                    }
                    updated = JsonValue.Create(asLong);
                    return true;
                }

                if (!double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out double asDouble)
                    || double.IsNaN(asDouble) || double.IsInfinity(asDouble))
                {
                    why = "needs a number";
                    return false;
                }
                updated = JsonValue.Create(asDouble);
                return true;

            case "bool":
                if (bool.TryParse(text, out bool asBool)) { updated = JsonValue.Create(asBool); return true; }
                why = "needs true or false";
                return false;

            case "text":
                updated = JsonValue.Create(text);
                return true;

            default:
                why = "unsupported field type";
                return false;
        }
    }

    /// <summary>Walk up from the binary until the repository is found, then use the debug saves folder.</summary>
    private static string FindSavesDirectory()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory != null)
        {
            if (File.Exists(Path.Combine(directory.FullName, GameProject)))
                return Path.Combine(directory.FullName, "bin", "Debug", "net8.0", "saves");
            directory = directory.Parent;
        }
        return Path.Combine(AppContext.BaseDirectory, "saves");
    }
}
