using System;
using System.Collections.Generic;
using System.IO;
using FluentAssertions;
using UsurperRemake.Systems;
using Xunit;

namespace UsurperReborn.Tests;

/// <summary>
/// GameData/Localization lets a mod ship translations for its own content.
/// The loader merges those flat key/value files after the official language
/// files, so a mod can add new IDs or override the translation of an ID it
/// replaces, without editing Localization/zh.json and colliding with another
/// mod's copy of that file.
/// </summary>
public class ModLocalizationTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "usurper-modloc-" + Guid.NewGuid().ToString("N"));

    public ModLocalizationTests() => Directory.CreateDirectory(_dir);

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch { }
    }

    private string WriteFile(string name, string json)
    {
        string path = Path.Combine(_dir, name);
        File.WriteAllText(path, json);
        return path;
    }

    [Fact]
    public void Adds_a_language_and_merges_keys()
    {
        var languages = new Dictionary<string, Dictionary<string, string>>();
        string file = WriteFile("zh.json", """
            {
              "_comment": "not a translation",
              "npc_dialogue.mod_line": "模组台词",
              "mod.equipment.200001.name": "模组之剑"
            }
            """);

        int merged = Loc.MergeModFileInto(languages, file, "zh");

        merged.Should().Be(2);
        languages.Should().ContainKey("zh");
        languages["zh"].Should().HaveCount(2);
        languages["zh"]["npc_dialogue.mod_line"].Should().Be("模组台词");
        languages["zh"].Should().ContainKey("mod.equipment.200001.name");
    }

    [Fact]
    public void Later_mod_file_overrides_an_official_or_earlier_key()
    {
        var languages = new Dictionary<string, Dictionary<string, string>>
        {
            ["zh"] = new() { ["dream.mod_dream.title"] = "官方旧标题", ["ui.keep"] = "保留" }
        };
        string file = WriteFile("mod.json", """
            {
              "dream.mod_dream.title": "模组新标题",
              "dream.mod_dream.content.0": "第一行"
            }
            """);

        int merged = Loc.MergeModFileInto(languages, file, "zh");

        merged.Should().Be(2);
        languages["zh"]["dream.mod_dream.title"].Should().Be("模组新标题");
        languages["zh"]["dream.mod_dream.content.0"].Should().Be("第一行");
        languages["zh"]["ui.keep"].Should().Be("保留");
    }

    [Fact]
    public void Empty_language_code_is_ignored()
    {
        var languages = new Dictionary<string, Dictionary<string, string>>();
        string file = WriteFile("x.json", """{ "a": "b" }""");

        Loc.MergeModFileInto(languages, file, "").Should().Be(0);
        languages.Should().BeEmpty();
    }
}
