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
        /// </summary>
        public static Said? TakeFor(string? npcName)
        {
            var said = _pending;
            if (said == null) return null;
            if (!string.IsNullOrEmpty(said.Target) && !string.IsNullOrEmpty(npcName)
                && !string.Equals(said.Target, npcName, StringComparison.OrdinalIgnoreCase))
                return null;
            _pending = null;
            return said;
        }

        /// <summary>Forget anything held (a new turn, a different location, a cancelled action).</summary>
        public static void Clear() => _pending = null;

        public static bool HasPending => _pending != null;
    }
}
