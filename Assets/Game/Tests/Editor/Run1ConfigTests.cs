using Game.Core;
using Game.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.Editor
{
    public class Run1ConfigTests
    {
        [Test]
        public void Run1ConfigLoadsFromResources()
        {
            Run1Config config = Run1ConfigLoader.Load();

            Assert.IsNotNull(config, "Config should load");
            Assert.AreEqual(1, config.schemaVersion);
            Assert.AreEqual(2400, config.maxSeconds);
            Assert.AreEqual(7.96f, config.prestigeMultiplier, 0.0001f);

            Assert.IsNotNull(config.buildings);
            Assert.AreEqual(4, config.buildings.Length);
            Assert.AreEqual("salvage_rig", config.buildings[0].id);

            Assert.IsNotNull(config.fixedPurchases);
            Assert.AreEqual(7, config.fixedPurchases.Length);

            FixedPurchaseData last = config.fixedPurchases[config.fixedPurchases.Length - 1];
            Assert.AreEqual("emp", last.id);
            Assert.IsTrue(last.endsRun);
        }
    }
}
