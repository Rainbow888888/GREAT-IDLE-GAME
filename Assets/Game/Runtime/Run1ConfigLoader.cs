using Game.Core;
using UnityEngine;

namespace Game.Runtime
{
    public static class Run1ConfigLoader
    {
        public static Run1Config Load()
        {
            TextAsset asset = Resources.Load<TextAsset>("balance/run1");
            if (asset == null)
            {
                throw new System.InvalidOperationException("Run1 config not found in Resources/balance/run1");
            }

            return JsonUtility.FromJson<Run1Config>(asset.text);
        }
    }
}
