using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.RegularExpressions;

namespace UsurperRemake.Editor;

/// <summary>
/// Chinese text for the standalone editor. The editor is a separate tool with its own vocabulary
/// (JSON fields, modding categories, validation messages), so it keeps its own catalogue instead of
/// growing the game's key list. English is the source and the fallback; the catalogue is display
/// only, so a translated choice is still saved with its original English value.
/// </summary>
internal static class EditorLoc
{
    private static readonly Dictionary<string, string> Zh = EditorZhCatalog.Map;
    private static readonly List<(Regex Pattern, string Translation)> Patterns = BuildPatterns();

    private static bool IsChinese =>
        string.Equals(GameConfig.Language, "zh", StringComparison.OrdinalIgnoreCase);

    /// <summary>Translate a whole static label. Unknown text stays as written.</summary>
    public static string T(string text)
    {
        if (string.IsNullOrEmpty(text) || !IsChinese) return text;
        if (Zh.TryGetValue(text, out var translated)) return translated;
        string key = Normalize(text);
        if (key != text && Zh.TryGetValue(key, out translated)) return translated;

        int leading = text.Length - text.TrimStart().Length;
        string body = text.Trim();
        foreach (var (pattern, translation) in Patterns)
        {
            var match = pattern.Match(Normalize(body));
            if (!match.Success) continue;
            var args = new object?[match.Groups.Count - 1];
            for (int i = 1; i < match.Groups.Count; i++) args[i - 1] = Exact(match.Groups[i].Value.Trim());
            try { return new string(' ', leading) + string.Format(CultureInfo.InvariantCulture, translation, args); }
            catch (FormatException) { }
        }

        // The shared pickers append a value to a label; translate the label, keep the value.
        const string keep = "(keep current: ";
        if (text.StartsWith(keep, StringComparison.Ordinal) && text.EndsWith(")"))
            return $"（保留当前：{text[keep.Length..^1]}）";
        const string current = "(current: ";
        int at = text.LastIndexOf(current, StringComparison.Ordinal);
        if (at >= 0 && text.EndsWith(")"))
            return $"{T(text[..at])}  （当前：{text[(at + current.Length)..^1]}）";

        return text;
    }

    /// <summary>Translate an interpolated format and fill its arguments.</summary>
    public static string F(string template, params object?[] args)
    {
        string format = template;
        if (IsChinese)
        {
            if (Zh.TryGetValue(template, out var translated)) format = translated;
            else if (Zh.TryGetValue(Normalize(template), out translated)) format = translated;
        }
        try
        {
            return string.Format(CultureInfo.InvariantCulture, format, args);
        }
        catch (FormatException)
        {
            return string.Format(CultureInfo.InvariantCulture, template, args);
        }
    }

    public static string F(FormattableString text) => F(text.Format, text.GetArguments());

    /// <summary>Translate a captured value only on an exact catalogue match.</summary>
    private static string Exact(string text)
    {
        if (Zh.TryGetValue(text, out var translated)) return translated;
        string key = Normalize(text);
        return Zh.TryGetValue(key, out translated) ? translated : text;
    }

    private static string Normalize(string text) =>
        Regex.Replace(text.Trim(), @"\s+", " ");

    private static List<(Regex, string)> BuildPatterns()
    {
        var patterns = new List<(Regex, string)>();
        var slot = new Regex(@"\{(\d+)(?:,-?\d+)?(?::[^}]*)?\}");
        foreach (var (key, translation) in Zh)
        {
            if (!key.Contains('{') || !translation.Contains('{')) continue;
            string literalOnly = slot.Replace(key, "");
            if (literalOnly.Length < 6 || !literalOnly.Any(char.IsLetter)) continue;
            var regex = new System.Text.StringBuilder("^");
            int at = 0;
            foreach (Match m in slot.Matches(key))
            {
                regex.Append(Regex.Escape(key[at..m.Index]).Replace("\\ ", "\\s+"));
                regex.Append("(.*?)");
                at = m.Index + m.Length;
            }
            regex.Append(Regex.Escape(key[at..]).Replace("\\ ", "\\s+")).Append('$');
            try { patterns.Add((new Regex(regex.ToString(), RegexOptions.CultureInvariant), translation)); }
            catch (ArgumentException) { }
        }
        return patterns.OrderByDescending(p => p.Item2.Length).ToList();
    }
}
