using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using FluentAssertions;
using UsurperRemake;
using UsurperRemake.Systems;
using UsurperRemake.UI;
using Xunit;

namespace UsurperReborn.Tests;

/// <summary>
/// The combat action menu is a fixed 41-column frame. A wide-script label or monster name must not
/// push its right border out; every row is measured in terminal columns, not UTF-16 code units.
/// </summary>
[Collection("SharedGameSingletons")]
public class CombatWideLayoutTests
{
    private const BindingFlags F = BindingFlags.NonPublic | BindingFlags.Instance;

    private static (CombatEngine engine, TerminalEmulator term, MemoryStream output) Engine()
    {
        var output = new MemoryStream();
        var term = new TerminalEmulator(new MemoryStream(), output);
        return (new CombatEngine(term), term, output);
    }

    private static string Shown(TerminalEmulator term, MemoryStream output)
    {
        term.StreamWriterInternal?.Flush();
        return Regex.Replace(Encoding.UTF8.GetString(output.ToArray()), "\u001b\\[[0-9;]*[A-Za-z]", "");
    }

    private static Character Hero() => new()
    {
        Name1 = "tester", Name2 = "Tester", Class = CharacterClass.Warrior, Level = 30, HP = 500, MaxHP = 500,
        AI = CharacterAI.Human, Healing = 3,
    };

    [Theory]
    [InlineData("en")]
    [InlineData("zh")]
    public void ActionMenu_EveryBorderRowStaysFortyOneColumns(string lang)
    {
        var previous = GameConfig.Language;
        GameConfig.Language = lang;
        try
        {
            var (engine, term, output) = Engine();
            var monster = new Monster { Name = lang == "zh" ? "哥布林首领" : "Goblin", Level = 2, HP = 20, MaxHP = 30, IsActive = true };
            typeof(CombatEngine).GetMethod("ShowCombatMenuStandard", F)!
                .Invoke(engine, new object?[] { Hero(), monster, null, false });
            string text = Shown(term, output);
            var rows = text.Split('\n').Select(line => line.TrimEnd('\r'))
                .Where(line => line.Length > 0 && "╔╠╚║".IndexOf(line[0]) >= 0)
                .ToList();
            rows.Should().NotBeEmpty();
            foreach (string row in rows)
                TextWidth.Width(row).Should().Be(41, $"the action menu border must not move: [{row}]");
        }
        finally
        {
            GameConfig.Language = previous;
        }
    }

    [Fact]
    public void QuickbarRow_StaysFortyOneColumns_WithAChineseName()
    {
        var (engine, term, output) = Engine();
        typeof(CombatEngine).GetMethod("WriteQuickbarBoxRows", F)!
            .Invoke(engine, new object?[] { "1", "强力打击 (15 体力)", true });
        string text = Shown(term, output);
        var rows = text.Split('\n').Select(line => line.TrimEnd('\r'))
            .Where(line => line.Length > 0)
            .ToList();
        rows.Should().NotBeEmpty();
        foreach (string row in rows)
            TextWidth.Width(row).Should().Be(41, $"the quickbar row must keep the menu frame: [{row}]");
    }

    [Theory]
    [InlineData("en")]
    [InlineData("zh")]
    public void DungeonActionMenu_EveryBorderRowStaysFortyOneColumns(string lang)
    {
        var previous = GameConfig.Language;
        GameConfig.Language = lang;
        try
        {
            var (engine, term, output) = Engine();
            typeof(CombatEngine).GetMethod("ShowDungeonCombatMenuStandard", F)!
                .Invoke(engine, new object?[]
                {
                    Hero(), false, false, new List<(string key, string name, bool available)>(), false, GodDomain.None,
                });
            string text = Shown(term, output);
            var rows = text.Split('\n').Select(line => line.TrimEnd('\r'))
                .Where(line => line.Length > 0 && "╔╠╚║".IndexOf(line[0]) >= 0)
                .ToList();
            rows.Should().NotBeEmpty();
            foreach (string row in rows)
                TextWidth.Width(row).Should().Be(41, $"the dungeon action menu border must not move: [{row}]");
        }
        finally
        {
            GameConfig.Language = previous;
        }
    }

    [Theory]
    [InlineData("en")]
    [InlineData("zh")]
    public void StatusPanel_HeaderAndRulesStaySixtyColumns(string lang)
    {
        var previous = GameConfig.Language;
        GameConfig.Language = lang;
        try
        {
            var (engine, term, output) = Engine();
            var monster = new Monster { Name = lang == "zh" ? "哥布林首领" : "Goblin", Level = 2, HP = 20, MaxHP = 30, IsActive = true };
            typeof(CombatEngine).GetMethod("DisplayCombatStatus", F)!
                .Invoke(engine, new object?[] { new List<Monster> { monster }, Hero(), 1 });
            string text = Shown(term, output);
            var rows = text.Split('\n').Select(line => line.TrimEnd('\r'))
                .Where(line => line.Length > 0 && "╔╠╚║".IndexOf(line[0]) >= 0)
                .ToList();
            rows.Should().NotBeEmpty();
            foreach (string row in rows.Where(row => row[0] != '║'))
                TextWidth.Width(row).Should().Be(60, $"the status frame must not move: [{row}]");
            foreach (string row in rows.Where(row => row[0] == '║'))
                TextWidth.Width(row).Should().BeLessThanOrEqualTo(79, $"a status row must fit one terminal line: [{row}]");
        }
        finally
        {
            GameConfig.Language = previous;
        }
    }
}
