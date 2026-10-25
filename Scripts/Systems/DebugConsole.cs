using System;
using System.Collections.Generic;
using System.Globalization;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// v1.3.9: the debug console behind <c>@ai</c>.
    ///
    /// The assistant may propose a command, but it is a person who runs it and this class that decides
    /// what a command is allowed to touch. A model never reaches a field directly: every path is looked
    /// up in a fixed table, every value is converted and range-checked, and an unknown path is refused
    /// with the list of the ones that exist. That keeps the surface small enough to reason about and
    /// keeps a save from depending on what a model happened to emit.
    /// </summary>
    public static class DebugConsole
    {
        private sealed class Field
        {
            public required string Name { get; init; }
            public required Func<Character, string> Get { get; init; }
            public Action<Character, string>? Set { get; init; }
            public string? Note { get; init; }
        }

        private static readonly List<Field> Fields = new()
        {
            new Field { Name = "player.name", Get = p => p.Name2 ?? p.Name1 ?? "" },
            new Field { Name = "player.level", Get = p => p.Level.ToString(),
                        Set = (p, v) => { if (TryInt(v, 1, 1000, out int n)) p.Level = n; } },
            new Field { Name = "player.gold", Get = p => p.Gold.ToString(),
                        Set = (p, v) => { if (TryLong(v, 0L, 999_999_999L, out long n)) p.Gold = n; } },
            new Field { Name = "player.hp", Get = p => p.HP.ToString(),
                        Set = (p, v) => { if (TryInt(v, 0, (int)Math.Min(int.MaxValue, Math.Max(1, p.MaxHP)), out int n)) p.HP = n; } },
            new Field { Name = "player.maxhp", Get = p => p.MaxHP.ToString(),
                        Set = (p, v) => { if (TryInt(v, 1, 999_999, out int n)) p.MaxHP = n; } },
            new Field { Name = "player.strength", Get = p => p.Strength.ToString(),
                        Set = (p, v) => { if (TryInt(v, 1, 9999, out int n)) p.Strength = n; } },
            new Field { Name = "player.defense", Get = p => p.Defense.ToString(),
                        Set = (p, v) => { if (TryInt(v, 0, 9999, out int n)) p.Defense = n; } },
            new Field { Name = "player.location", Get = p => p.CurrentLocation ?? "" },
            new Field { Name = "player.class", Get = p => p.ClassName ?? "" },
        };

        /// <summary>One-line help for the console, used by the assistant and by the refusal message.</summary>
        public static string Help()
            => "get <path>  |  set <path> <value>  |  paths: " + string.Join(", ", Fields.ConvertAll(f => f.Name));

        /// <summary>
        /// Run one command. Returns false with a reason when the command is not understood or not
        /// allowed; nothing is changed in that case.
        /// </summary>
        public static bool TryRun(string command, Character player, out string output)
        {
            output = "";
            if (string.IsNullOrWhiteSpace(command)) { output = "empty command"; return false; }
            if (player == null) { output = "no player"; return false; }

            var parts = command.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
            string verb = parts[0].ToLowerInvariant();

            if (verb == "help")
            {
                output = Help();
                return true;
            }

            if (parts.Length < 2) { output = Help(); return false; }
            string path = parts[1].ToLowerInvariant();
            var field = Fields.Find(f => f.Name == path);
            if (field == null)
            {
                output = $"no such path: {path}\n{Help()}";
                return false;
            }

            if (verb == "get")
            {
                output = $"{field.Name} = {field.Get(player)}";
                return true;
            }

            if (verb == "set")
            {
                if (field.Set == null) { output = $"{field.Name} is read-only"; return false; }
                if (parts.Length < 3) { output = "set needs a value"; return false; }
                string before = field.Get(player);
                string value = string.Join(' ', parts[2..]);
                field.Set(player, value);
                string after = field.Get(player);
                output = $"{field.Name}: {before} -> {after}";
                if (before == after) output += "  (value rejected: out of range or not a number)";
                DebugLogger.Instance.LogInfo("DEBUG", $"console: {command} => {output}");
                return before != after;
            }

            output = Help();
            return false;
        }

        /// <summary>True when the command only reads, so it needs no confirmation.</summary>
        public static bool IsReadOnly(string command)
        {
            var t = command.TrimStart();
            return t.StartsWith("get ", StringComparison.OrdinalIgnoreCase)
                || t.Equals("help", StringComparison.OrdinalIgnoreCase);
        }

        private static bool TryInt(string text, int min, int max, out int value)
            => int.TryParse(text.Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out value)
               && value >= min && value <= max;

        private static bool TryLong(string text, long min, long max, out long value)
            => long.TryParse(text.Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out value)
               && value >= min && value <= max;
    }
}
