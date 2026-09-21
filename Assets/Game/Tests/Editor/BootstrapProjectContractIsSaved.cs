using System.Collections;
using System.Reflection;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;
using TMPro;

namespace Game.Tests.Editor
{
    public class BootstrapProjectContractIsSaved
    {
        [UnityTest]
        public IEnumerator RunAllChecks()
        {
            var urpAsset = GraphicsSettings.defaultRenderPipeline as UniversalRenderPipelineAsset;
            Assert.IsNotNull(urpAsset, "GraphicsSettings.defaultRenderPipeline is not a URP asset.");

            var renderer = urpAsset.GetRenderer(0);
            Assert.IsNotNull(renderer, "URP asset default renderer is null.");
            Assert.AreEqual("Renderer2D", renderer.GetType().Name, $"Default renderer is {renderer.GetType().Name}, expected Renderer2D.");

            var rendererDataPath = "Assets/Game/Rendering/Renderer2D.asset";
            var rendererData = AssetDatabase.LoadAssetAtPath<Renderer2DData>(rendererDataPath);
            Assert.IsNotNull(rendererData, "Renderer2DData asset not found.");

            AssertAllQualityLevelsUse(urpAsset);

            var scenes = EditorBuildSettings.scenes;
            Assert.AreEqual(1, scenes.Length, "Build Settings must contain exactly one scene.");
            Assert.IsTrue(scenes[0].enabled, "Bootstrap scene must be enabled in Build Settings.");
            Assert.AreEqual("Assets/Game/Scenes/Bootstrap.unity", scenes[0].path);

            EditorSceneManager.OpenScene("Assets/Game/Scenes/Bootstrap.unity", OpenSceneMode.Single);
            yield return null;

            var cameras = Object.FindObjectsByType<Camera>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            Assert.AreEqual(1, cameras.Length, "Scene must contain exactly one Camera.");
            Assert.AreEqual("MainCamera", cameras[0].gameObject.name);
            Assert.IsTrue(cameras[0].orthographic, "Main camera must be orthographic.");

            var canvases = Object.FindObjectsByType<Canvas>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            Assert.AreEqual(1, canvases.Length, "Scene must contain exactly one Canvas.");
            var canvas = canvases[0];
            Assert.AreEqual(RenderMode.ScreenSpaceOverlay, canvas.renderMode);
            Assert.IsTrue(canvas.isRootCanvas, "Canvas must be a root canvas.");
            Assert.IsTrue(canvas.enabled, "Canvas must be enabled.");

            Canvas.ForceUpdateCanvases();
            Assert.IsTrue(canvas.transform.localScale.sqrMagnitude > 0f, "Canvas must have a non-zero scale after a canvas update.");

            var scaler = canvas.GetComponent<UnityEngine.UI.CanvasScaler>();
            Assert.IsNotNull(scaler);
            Assert.AreEqual(UnityEngine.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize, scaler.uiScaleMode);
            Assert.AreEqual(new Vector2(1920f, 1080f), scaler.referenceResolution);
            Assert.AreEqual(UnityEngine.UI.CanvasScaler.ScreenMatchMode.MatchWidthOrHeight, scaler.screenMatchMode);
            Assert.AreEqual(0.5f, scaler.matchWidthOrHeight);

            Assert.IsNotNull(canvas.GetComponent<UnityEngine.UI.GraphicRaycaster>(), "Canvas must have a GraphicRaycaster.");

            var titleGO = GameObject.Find("Title");
            Assert.IsNotNull(titleGO, "Scene must contain a Title GameObject.");
            Assert.IsTrue(titleGO.activeInHierarchy, "Title must be active.");
            Assert.IsTrue(titleGO.transform.IsChildOf(canvas.transform), "Title must be a child of the Canvas.");

            var tmp = titleGO.GetComponent<TextMeshProUGUI>();
            Assert.IsNotNull(tmp, "Title must have TextMeshProUGUI.");
            Assert.AreEqual("GREAT IDLE GAME", tmp.text);
            Assert.AreEqual(72f, tmp.fontSize);
            Assert.AreEqual(Color.white, tmp.color);
            Assert.IsFalse(tmp.raycastTarget);
            Assert.IsTrue(tmp.rectTransform.sizeDelta.sqrMagnitude > 0f, "Title RectTransform must have non-zero size.");
            Assert.IsTrue(tmp.rectTransform.localScale.sqrMagnitude > 0f, "Title scale must be non-zero.");

            Assert.AreEqual("Klarus", PlayerSettings.companyName);
            Assert.AreEqual("GREAT IDLE GAME", PlayerSettings.productName);
            Assert.AreEqual("com.klarus.greatidlegame", PlayerSettings.GetApplicationIdentifier(NamedBuildTarget.Standalone));
            Assert.AreEqual(1, GetActiveInputHandler(), "Active input handler must be Input System only.");
        }

        private void AssertAllQualityLevelsUse(UniversalRenderPipelineAsset asset)
        {
            var method = typeof(QualitySettings).GetMethod("GetQualityLevelRenderPipeline", BindingFlags.Public | BindingFlags.Static);
            int original = QualitySettings.GetQualityLevel();
            try
            {
                for (int i = 0; i < QualitySettings.count; i++)
                {
                    RenderPipelineAsset levelAsset;
                    if (method != null)
                    {
                        levelAsset = method.Invoke(null, new object[] { i }) as RenderPipelineAsset;
                    }
                    else
                    {
                        QualitySettings.SetQualityLevel(i, false);
                        levelAsset = QualitySettings.renderPipeline;
                    }
                    Assert.AreEqual(asset, levelAsset, $"Quality level {QualitySettings.names[i]} does not reference the URP asset.");
                }
            }
            finally
            {
                QualitySettings.SetQualityLevel(original, false);
            }
        }

        private int GetActiveInputHandler()
        {
            var settingsAsset = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>("ProjectSettings/ProjectSettings.asset");
            if (settingsAsset == null)
                return -1;
            var so = new SerializedObject(settingsAsset);
            var prop = so.FindProperty("activeInputHandler");
            return prop != null ? prop.intValue : -1;
        }
    }
}
