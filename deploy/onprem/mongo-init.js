const fs = require('fs');
const password = fs.readFileSync(process.env.MONGO_APP_PASSWORD_FILE, 'utf8').trim();
if (password.length < 24) throw new Error('Application password must be at least 24 characters');
db.getSiblingDB('ocuforge').createUser({user:'ocuforge_app',pwd:password,roles:[{role:'readWrite',db:'ocuforge'}]});
