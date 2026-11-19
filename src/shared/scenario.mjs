// Fixed version-1 configuration. Keep aligned with docs/fixtures/scenario-v1.json.
export const SCENARIO = {
  "scenarioId": "mist-river-dry-spring",
  "schemaVersion": 1,
  "ruleVersion": 1,
  "scenarioVersion": 1,
  "seed": 20261118,
  "day": 0,
  "generatedResidents": 30,
  "digitalResidentLimit": 1,
  "resources": {
    "food": 180,
    "water": 180,
    "wood": 100,
    "treasury": 1000
  },
  "communityTrust": 60,
  "externalSpent": 0,
  "jobs": {
    "farmer": 10,
    "waterWorker": 10,
    "resident": 10
  },
  "agentDefaults": {
    "energy": 70,
    "hunger": 30,
    "waterNeed": 30,
    "cash": 20
  },
  "digitalDefaults": {
    "energy": 70,
    "hunger": 30,
    "waterNeed": 30,
    "cash": 0
  },
  "relationshipDefaults": {
    "trust": 50,
    "affinity": 50
  },
  "facilities": [
    {
      "facilityId": "farm-01",
      "type": "farm",
      "open": true,
      "capacity": 31
    },
    {
      "facilityId": "well-01",
      "type": "well",
      "open": true,
      "capacity": 31
    },
    {
      "facilityId": "market-01",
      "type": "market",
      "open": true,
      "capacity": 31
    },
    {
      "facilityId": "plaza-01",
      "type": "plaza",
      "open": true,
      "capacity": 10
    },
    {
      "facilityId": "home-01",
      "type": "home",
      "open": true,
      "capacity": 31
    }
  ],
  "proposal": {
    "proposalId": "repair-well-01",
    "version": 1,
    "status": "OPEN",
    "cost": 120,
    "waterEffect": 30,
    "trustEffect": 5,
    "proposerAgentId": "resident-001",
    "ballots": []
  }
};
