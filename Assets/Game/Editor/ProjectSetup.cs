using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UI;
using TMPro;

namespace Game.Editor
{
    public static class ProjectSetup
    {
        private const string RenderingDir = "Assets/Game/Rendering";
        private const string UrpAssetPath = RenderingDir + "/URP_2D.asset";
        private const string RendererPath = RenderingDir + "/Renderer2D.asset";
        private const string ScenePath = "Assets/Game/Scenes/Bootstrap.unity";

        [MenuItem("GREAT/Project Setup")]
        public static void Run()
        {
            try
            {
                Directory.CreateDirectory(RenderingDir);
                Directory.CreateDirectory("Assets/Game/Scenes");

                ImportTmpEssentials();
                var urpAsset = EnsureUrpAsset();
                ApplyGraphicsSettings(urpAsset);
                ApplyPlayerSettings();
                EnsureBootstrapScene();
                EnsureBuildSettings();

                AssetDatabase.SaveAssets();
                EditorApplication.Exit(0);
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ProjectSetup] Failed: {ex}");
                EditorApplication.Exit(1);
            }
        }

        private static void ImportTmpEssentials()
        {
            if (AssetDatabase.LoadAssetAtPath<TMP_Settings>("Assets/TextMesh Pro/Resources/TMP Settings.asset") != null)
            {
                Debug.Log("[ProjectSetup] TMP Essentials already imported.");
                return;
            }

            Debug.Log("[ProjectSetup] Importing TMP Essentials...");
            TMP_PackageResourceImporter.ImportResources(true, false, false);
            AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
        }

        private static UniversalRenderPipelineAsset EnsureUrpAsset()
        {
            var existing = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(UrpAssetPath);
            if (existing != null)
            {
                Debug.Log("[ProjectSetup] URP asset already exists.");
                return existing;
            }

            var rendererData = ScriptableObject.CreateInstance<Renderer2DData>();
            SetDefaultPostProcessData(rendererData);
            AssetDatabase.CreateAsset(rendererData, RendererPath);

            var urpAsset = UniversalRenderPipelineAsset.Create(rendererData);
            AssetDatabase.CreateAsset(urpAsset, UrpAssetPath);

            AssetDatabase.SaveAssets();
            Debug.Log("[ProjectSetup] Created URP 2D asset.");
            return urpAsset;
        }

        private static void SetDefaultPostProcessData(Renderer2DData rendererData)
        {
            try
            {
                var urpAssembly = typeof(Renderer2DData).Assembly;
                var postProcessDataType = urpAssembly.GetType("UnityEngine.Rendering.Universal.PostProcessData");
                if (postProcessDataType == null)
                    return;

                var method = postProcessDataType.GetMethod("GetDefaultPostProcessData", BindingFlags.NonPublic | BindingFlags.Static);
                if (method == null)
                    return;

                var defaultData = method.Invoke(null, null);
                var property = typeof(Renderer2DData).GetProperty("postProcessData", BindingFlags.NonPublic | BindingFlags.Instance);
                property?.SetValue(rendererData, defaultData);
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[ProjectSetup] Could not set default post-process data: {ex.Message}");
            }
        }

        private static void ApplyGraphicsSettings(UniversalRenderPipelineAsset urpAsset)
        {
            GraphicsSettings.defaultRenderPipeline = urpAsset;
            var globalSettings = GraphicsSettings.GetSettingsForRenderPipeline(typeof(UniversalRenderPipeline));
            if (globalSettings != null)
                EditorUtility.SetDirty(globalSettings);

            for (int i = 0; i < QualitySettings.count; i++)
            {
                QualitySettings.SetQualityLevel(i, false);
                QualitySettings.renderPipeline = urpAsset;
            }
            QualitySettings.SetQualityLevel(0, false);

            var renderer = urpAsset.GetRenderer(0);
            if (renderer == null)
                throw new InvalidOperationException("URP asset has no default renderer.");
            if (renderer.GetType().Name != "Renderer2D")
                throw new InvalidOperationException($"Default renderer is {renderer.GetType().Name}, expected Renderer2D.");

            Debug.Log("[ProjectSetup] Graphics and Quality settings applied.");
        }

        private static void ApplyPlayerSettings()
        {
            PlayerSettings.companyName = "Klarus";
            PlayerSettings.productName = "GREAT IDLE GAME";
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Standalone, "com.klarus.greatidlegame");

            var settingsAsset = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>("ProjectSettings/ProjectSettings.asset");
            if (settingsAsset != null)
            {
                var so = new SerializedObject(settingsAsset);
                var prop = so.FindProperty("activeInputHandler");
                if (prop != null)
                {
                    prop.intValue = 1; // Input System only
                    so.ApplyModifiedProperties();
                }
            }

            Debug.Log("[ProjectSetup] Player settings applied.");
        }

        private static void EnsureBootstrapScene()
        {
            bool found = false;
            foreach (var s in EditorSceneManager.GetSceneManagerSetup())
            {
                if (s.path == ScenePath)
                {
                    found = true;
                    break;
                }
            }

            var scene = found
                ? EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single)
                : EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            foreach (var go in scene.GetRootGameObjects())
            {
                UnityEngine.Object.DestroyImmediate(go);
            }

            var mainCamera = new GameObject("MainCamera") { tag = "MainCamera" };
            var camera = mainCamera.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color32(0x10, 0x13, 0x18, 0xff);
            camera.orthographic = true;
            camera.orthographicSize = 5f;
            mainCamera.transform.position = new Vector3(0f, 0f, -10f);
            EditorSceneManager.MoveGameObjectToScene(mainCamera, scene);

            var canvasGO = new GameObject("Canvas");
            EditorSceneManager.MoveGameObjectToScene(canvasGO, scene);
            var canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;

            var scaler = canvasGO.AddComponent<UnityEngine.UI.CanvasScaler>();
            scaler.uiScaleMode = UnityEngine.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.screenMatchMode = UnityEngine.UI.CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            canvasGO.AddComponent<UnityEngine.UI.GraphicRaycaster>();

            var titleGO = new GameObject("Title");
            titleGO.transform.SetParent(canvasGO.transform, false);
            var titleRect = titleGO.AddComponent<RectTransform>();
            titleRect.anchorMin = new Vector2(0.5f, 0.5f);
            titleRect.anchorMax = new Vector2(0.5f, 0.5f);
            titleRect.anchoredPosition = Vector2.zero;
            titleRect.sizeDelta = new Vector2(900f, 160f);
            titleRect.localScale = Vector3.one;

            var tmp = titleGO.AddComponent<TextMeshProUGUI>();
            tmp.text = "GREAT IDLE GAME";
            tmp.fontSize = 72f;
            tmp.color = Color.white;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.raycastTarget = false;
            tmp.font = FindTmpFontAsset();

            var canvasRect = canvasGO.GetComponent<RectTransform>();
            canvasRect.localScale = Vector3.one;

            if (!Directory.Exists("Assets/Game/Scenes"))
                Directory.CreateDirectory("Assets/Game/Scenes");
            EditorSceneManager.SaveScene(scene, ScenePath);

            Debug.Log("[ProjectSetup] Bootstrap scene saved.");
        }

        private static void EnsureBuildSettings()
        {
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(ScenePath, true)
            };
            Debug.Log("[ProjectSetup] Build settings applied.");
        }

        private static TMP_FontAsset FindTmpFontAsset()
        {
            string[] guids = AssetDatabase.FindAssets("t:TMP_FontAsset", new[] { "Assets/TextMesh Pro" });
            foreach (var guid in guids)
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (path.Contains("LiberationSans"))
                    return AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
            }
            if (guids.Length > 0)
                return AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(AssetDatabase.GUIDToAssetPath(guids[0]));
            return null;
        }
    }
}
