// MongoDB Replica Set Initialization Script
print('Starting MongoDB replica set initialization...');

// Wait for MongoDB to be ready
sleep(5000);

try {
    // Check if replica set is already initialized
    var status = rs.status();
    print('Replica set already initialized');
} catch (e) {
    print('Initializing replica set...');
    
    // Initialize replica set
    rs.initiate({
        _id: "fok-replica-set",
        members: [
            {
                _id: 0,
                host: "mongodb-primary:27017",
                priority: 2
            }
        ]
    });
    
    // Wait for primary to be elected
    print('Waiting for primary to be elected...');
    sleep(10000);
    
    // Add secondary members
    print('Adding secondary members...');
    
    rs.add({
        _id: 1,
        host: "mongodb-secondary-1:27017",
        priority: 1
    });
    
    rs.add({
        _id: 2,
        host: "mongodb-secondary-2:27017",
        priority: 1
    });
    
    // Wait for replica set to stabilize
    print('Waiting for replica set to stabilize...');
    sleep(15000);
    
    print('Replica set configuration:');
    printjson(rs.conf());
    
    print('Replica set status:');
    printjson(rs.status());
}

// Create application database and user
print('Creating application database and user...');

// Switch to admin database
db = db.getSiblingDB('admin');

// Create application user
db.createUser({
    user: process.env.MONGO_USERNAME || 'fokbot',
    pwd: process.env.MONGO_PASSWORD || 'fokbot123',
    roles: [
        { role: 'readWrite', db: process.env.MONGO_DB_NAME || 'fok_bot' },
        { role: 'dbAdmin', db: process.env.MONGO_DB_NAME || 'fok_bot' }
    ]
});

// Switch to application database
db = db.getSiblingDB(process.env.MONGO_DB_NAME || 'fok_bot');

// Create collections with indexes
print('Creating collections and indexes...');

// Users collection
db.createCollection('users');
db.users.createIndex({ 'telegram_id': 1 }, { unique: true });
db.users.createIndex({ 'created_at': 1 });
db.users.createIndex({ 'last_activity': 1 });

// FOKs collection
db.createCollection('foks');
db.foks.createIndex({ 'name': 1 });
db.foks.createIndex({ 'district': 1 });
db.foks.createIndex({ 'sports': 1 });
db.foks.createIndex({ 'is_active': 1 });

// Applications collection
db.createCollection('applications');
db.applications.createIndex({ 'user_id': 1 });
db.applications.createIndex({ 'fok_id': 1 });
db.applications.createIndex({ 'status': 1 });
db.applications.createIndex({ 'created_at': 1 });
db.applications.createIndex({ 'sport': 1 });

// Sports collection
db.createCollection('sports');
db.sports.createIndex({ 'name': 1 }, { unique: true });
db.sports.createIndex({ 'is_active': 1 });

// Districts collection
db.createCollection('districts');
db.districts.createIndex({ 'name': 1 }, { unique: true });
db.districts.createIndex({ 'is_active': 1 });

print('MongoDB replica set initialization completed successfully!');
print('Replica set members:');
rs.status().members.forEach(function(member) {
    print('- ' + member.name + ' (' + member.stateStr + ')');
});