using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Game.Editor
{
    public static class BuildWindows
    {
        private const string OutputPath = "Builds/Windows/GREAT-IDLE-GAME.exe";
        private const string ScenePath = "Assets/Game/Scenes/Bootstrap.unity";

        public static void Build()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(OutputPath));

            var buildPlayerOptions = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            };

            BuildReport report = BuildPipeline.BuildPlayer(buildPlayerOptions);
            BuildSummary summary = report.summary;

            if (summary.result == BuildResult.Succeeded)
            {
                Debug.Log($"[BuildWindows] Build succeeded: {summary.totalSize} bytes.");
                EditorApplication.Exit(0);
            }
            else
            {
                Debug.LogError($"[BuildWindows] Build failed: {summary.result}");
                EditorApplication.Exit(1);
            }
        }
    }
}
