using System;

namespace Game.Core
{
    [Serializable]
    public class Run1Config
    {
        public int schemaVersion;
        public float tickSeconds;
        public float maxSeconds;
        public float prestigeMultiplier;
        public ManualActionData manualAction;
        public WorkerData worker;
        public BuildingData[] buildings;
        public FixedPurchaseData[] fixedPurchases;
    }

    [Serializable]
    public class ManualActionData
    {
        public float @yield;
        public float cooldownSeconds;
        public string stopsAfterPurchaseId;
    }

    [Serializable]
    public class WorkerData
    {
        public string id;
        public float baseCost;
        public float costGrowth;
        public float baseRate;
        public MilestoneData[] milestones;
    }

    [Serializable]
    public class MilestoneData
    {
        public int count;
        public float totalMultiplier;
    }

    [Serializable]
    public class BuildingData
    {
        public string id;
        public float baseCost;
        public float costGrowth;
        public float baseOutput;
        public float outputGrowth;
        public int maxLevel;
    }

    [Serializable]
    public class FixedPurchaseData
    {
        public string id;
        public float cost;
        public string category;
        public bool endsRun;
    }
}
