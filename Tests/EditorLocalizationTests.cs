using FluentAssertions;
using UsurperRemake;
using UsurperRemake.Editor;
using Xunit;

namespace UsurperReborn.Tests;

[Collection("SharedGameSingletons")]
public class EditorLocalizationTests
{
    [Fact]
    public void ChineseCatalog_TranslatesStaticMenusAndDynamicRows()
    {
        string previous = GameConfig.Language;
        GameConfig.Language = "zh";
        try
        {
            EditorLoc.T("Main Menu").Should().Be("主菜单");
            EditorLoc.T("Kids: 3").Should().Be("子女数：3");
            EditorLoc.T("View inventory (2 items)").Should().Be("查看物品栏（2 件）");
            EditorLoc.F("Initialization failed: {0}", "boom").Should().Be("初始化失败：boom");
            EditorLoc.T("Player Saves            — edit characters (stats, inventory, quests, companions, etc.)")
                .Should().StartWith("玩家存档");
            EditorLoc.T("This string is not in the catalogue").Should().Be("This string is not in the catalogue");
        }
        finally
        {
            GameConfig.Language = previous;
        }
    }

    [Fact]
    public void EnglishEditor_KeepsTheSourceText()
    {
        string previous = GameConfig.Language;
        GameConfig.Language = "en";
        try
        {
            EditorLoc.T("Main Menu").Should().Be("Main Menu");
            EditorLoc.F("Initialization failed: {0}", "boom").Should().Be("Initialization failed: boom");
        }
        finally
        {
            GameConfig.Language = previous;
        }
    }
}
