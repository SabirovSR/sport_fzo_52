// Initialize MongoDB Replica Set
rs.initiate({
  _id: "fok_replica",
  members: [
    {
      _id: 0,
      host: "mongodb-primary:27017",
      priority: 2
    },
    {
      _id: 1,
      host: "mongodb-secondary1:27017",
      priority: 1
    },
    {
      _id: 2,
      host: "mongodb-secondary2:27017",
      priority: 1
    },
    {
      _id: 3,
      host: "mongodb-arbiter:27017",
      arbiterOnly: true
    }
  ]
});

// Wait for replica set to be ready
sleep(5000);

// Check replica set status
rs.status();

print("Replica set initialization completed");