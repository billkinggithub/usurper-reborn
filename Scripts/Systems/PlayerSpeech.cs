using System;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// v1.3.9: the player's own words, waiting to be heard.
    ///
    /// When a free-form action carries speech ("you put on the armour and tell him ..."), the words and
    /// the tone are held here until the conversation with that NPC actually opens, so the NPC answers
    /// what the player said rather than a menu choice. Anything not collected by the end of the turn is
    /// dropped: a line meant for one person should not be delivered to the next.
    /// </summary>
    public static class PlayerSpeech
    {
        public sealed class Said
        {
            public required string Text { get; init; }
            public string? Target { get; init; }
            public string? Tone { get; init; }
        }

        private static Said? _pending;

        /// <summary>Hold what the player said for the next conversation with that NPC.</summary>
        public static void Hold(Said said)
        {
            _pending = said;
            DebugLogger.Instance.LogInfo("AI", $"player speech held for '{said.Target ?? "?"}': tone={said.Tone ?? "none"}");
        }

        /// <summary>
        /// Take the held words when they are addressed to this NPC. A line addressed to someone else is
        /// left alone, and a line with no target is given to whoever is spoken to first.
        ///
        /// v1.3.9: the match is forgiving, because the name comes from a model reading the screen. It
        /// wrote "Vex" for an NPC called "Vex the Merciless", and an exact comparison meant the words
        /// were never delivered. Either name containing the other counts, from three characters up.
        /// </summary>
        public static Said? TakeFor(string? npcName)
        {
            var said = _pending;
            if (said == null) return null;
            if (string.IsNullOrEmpty(said.Target) || string.IsNullOrEmpty(npcName)) { _pending = null; return said; }
            if (!NamesMatch(said.Target, npcName)) return null;
            _pending = null;
            return said;
        }

        internal static bool NamesMatch(string a, string b)
        {
            string x = a.Trim(), y = b.Trim();
            if (x.Length == 0 || y.Length == 0) return false;
            if (string.Equals(x, y, StringComparison.OrdinalIgnoreCase)) return true;
            if (x.Length < 3 || y.Length < 3) return false;
            return x.Contains(y, StringComparison.OrdinalIgnoreCase)
                   || y.Contains(x, StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>Forget anything held (a new turn, a different location, a cancelled action).</summary>
        public static void Clear() => _pending = null;

        public static bool HasPending => _pending != null;
    }
}
