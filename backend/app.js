const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors'); 
const app = express();
require('dotenv').config();
const PORT = process.env.PORT || 8080;
require('./config/dbConfig');


const routes = require('./routes');
// Middleware to enable CORS
app.use(cors());


app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(bodyParser.json());


app.use('/api', routes);

app.listen(PORT,()=>{
    console.log(`Server listening on port ${PORT}`);
})
