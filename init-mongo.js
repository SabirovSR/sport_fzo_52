// MongoDB initialization script
db = db.getSiblingDB('fok_bot');

// Create collections with indexes
db.createCollection('users');
db.users.createIndex({ "telegram_id": 1 }, { unique: true });
db.users.createIndex({ "phone": 1 });
db.users.createIndex({ "is_admin": 1 });

db.createCollection('foks');
db.foks.createIndex({ "name": 1 });
db.foks.createIndex({ "district": 1 });
db.foks.createIndex({ "sports": 1 });
db.foks.createIndex({ "is_active": 1 });

db.createCollection('applications');
db.applications.createIndex({ "user_id": 1 });
db.applications.createIndex({ "fok_id": 1 });
db.applications.createIndex({ "status": 1 });
db.applications.createIndex({ "created_at": 1 });

db.createCollection('districts');
db.districts.createIndex({ "name": 1 }, { unique: true });

db.createCollection('sports');
db.sports.createIndex({ "name": 1 }, { unique: true });

// Insert sample districts
db.districts.insertMany([
    { name: "Центральный район", is_active: true },
    { name: "Северный район", is_active: true },
    { name: "Южный район", is_active: true },
    { name: "Восточный район", is_active: true },
    { name: "Западный район", is_active: true }
]);

// Insert sample sports
db.sports.insertMany([
    { name: "Футбол", is_active: true },
    { name: "Баскетбол", is_active: true },
    { name: "Волейбол", is_active: true },
    { name: "Плавание", is_active: true },
    { name: "Теннис", is_active: true },
    { name: "Хоккей", is_active: true },
    { name: "Гимнастика", is_active: true },
    { name: "Борьба", is_active: true }
]);

print('Database initialized successfully');