const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const sqlite3 = require('sqlite3').verbose();
const { open } = require('sqlite');
const readline = require('readline');
const webp = require('webp-converter');
const fse = require('fs-extra');

const python_tools = require('./python-tools/python-tools');
const config = require('./config.json');

const equipment_dictionary = config["equipment_dictionary"];
const quest_dictionary = config["quest_dictionary"];
const database_dir = config["database"]["directory"];
const extract_dir = config["database"]["download_directory"];
const css_path = path.join(config["system"]["output_directory"], 'css', 'data.css');

run();

function run() {
    update_database().then(() => {
        console.log('SUCCESSFULLY UPDATED DATABASE');
        setup_files();
    });
    function setup_files() {
        const pqh_dir = config["system"]["priconne-quest-helper_directory"];
        const setup_dir = config["system"]["setup_directory"];
        const output_dir = config["system"]["output_directory"];

        // MAKE SURE SETUP/OUTPUT DIRECTORIES ARE AVAILABLE AND EMPTY
        confirm_empty_directory(setup_dir);
        confirm_empty_directory(output_dir);

        // COPY REQUIRED priconne-quest-helper FILES
        const character_data_path = path.join(pqh_dir, 'data', 'character_data.json'),
            equipment_data_path = path.join(pqh_dir, 'data', 'equipment_data.json'),
            dictionary_path = path.join(pqh_dir, 'data', 'dictionary.json'),
            jp_lang_path = path.join(pqh_dir, 'language', 'ja-JP.json');
        if (!fs.existsSync(character_data_path) ||
            !fs.existsSync(equipment_data_path) ||
            !fs.existsSync(dictionary_path) ||
            !fs.existsSync(jp_lang_path)) {
            console.log('A REQUIRED FILE IS MISSING ; CHECK THE config.json system.priconne-quest-helper_directory VALUE.\n' +
                '-', character_data_path, '\n' +
                '-', equipment_data_path, '\n' +
                '-', dictionary_path, '\n' +
                '-', jp_lang_path, '\n');
            return;
        }
        else {
            fs.copyFileSync(character_data_path, path.join(setup_dir, 'character_data.json'));
            fs.copyFileSync(equipment_data_path, path.join(setup_dir, 'equipment_data.json'));
            fs.copyFileSync(dictionary_path, path.join(setup_dir, 'dictionary.json'));
            fs.copyFileSync(jp_lang_path, path.join(setup_dir, 'ja-JP.json'));

            console.log('SUCCESSFULLY COPIED ALL REQUIRED priconne-quest-helper FILES')
        }

        // CREATE JSON FILES
        write_equipment_data().then(() => {
            write_character_data().then(() => {
                write_quest_data().then(() => {
                    get_new_images().then(() => {
                        create_spritesheets().then(() => {
                            update_dictionary();
                            console.log('UPDATE COMPLETE!');
                        });
                    });
                });
            });
        });
    }
}

function update_database() {
    return new Promise(async function(resolve) {
        // CHECK IF DATABASE DIRECTORY EXISTS
        if (!fs.existsSync(database_dir)) {
            fs.mkdirSync(database_dir);
        }

        // READ CURRENT DATABASE VERSION
        let current_version;
        const version_file = path.join(database_dir, 'version');
        if (fs.existsSync(version_file)) {
            // DATABASE VERSION FILE EXISTS
            const json = JSON.parse(fs.readFileSync(version_file, 'utf8'));
            current_version = {
                truth_version: json['truth_version'],
                hash: json['hash'],
            };
            console.log('EXISTING VERSION FILE FOUND: CURRENT TRUTH VERSION =', current_version['truth_version']);
        }
        else {
            // DATABASE VERSION FILE DOES NOT EXIST, START FROM SCRATCH
            current_version = {
                truth_version: config["database"]["default_truth_version"],
                hash: ''
            };
            console.log('VERSION FILE NOT FOUND. USING TRUTH VERSION', current_version['truth_version']);
        }

        console.log('CHECKING FOR DATABASE UPDATES...');
        let truth_version = parseInt(current_version['truth_version']);
        (async () => {
            function request(guess) {
                return new Promise((resolve) => {
                    http.request({
                        host: 'prd-priconne-redive.akamaized.net',
                        path: '/dl/Resources/' + guess + '/Jpn/AssetBundles/iOS/manifest/manifest_assetmanifest',
                        method: 'GET',
                    }, (res) => {
                        resolve(res);
                    }).end();
                });
            }

            // FIND NEW TRUTH VERSION
            const max_test = config["database"]["max_test_amount"];
            const test_multiplier = config["database"]["test_multiplier"];
            for (let i = 1 ; i <= max_test ; i++) {
                const guess = truth_version + (i * test_multiplier);
                console.log('[GUESS]'.padEnd(10), guess);
                const res = await request(guess);
                if (res.statusCode === 200) {
                    console.log('[SUCCESS]'.padEnd(10), guess, ' RETURNED STATUS CODE 200 (VALID TRUTH VERSION)');

                    // RESET LOOP
                    truth_version = guess;
                    i = 1;
                }
            }
        })().then(() => {
            console.log('VERSION CHECK COMPLETE ; LATEST TRUTH VERSION =', truth_version);

            // CHECK IF LATEST TRUTH VERSION IS DIFFERENT FROM CURRENT
            if (truth_version === current_version['truth_version']) {
                console.log('NO UPDATE FOUND, MUST BE ON THE LATEST VERSION!');
            }

            let bundle = '';
            http.request({
                host: 'prd-priconne-redive.akamaized.net',
                path: '/dl/Resources/' + truth_version + '/Jpn/AssetBundles/Windows/manifest/masterdata_assetmanifest',
                method: 'GET',
            }, (res) => {
                res.on('data', function(chunk) {
                    bundle += Buffer.from(chunk).toString();
                });
                res.on('end', () => {
                    const b = bundle.split(',');
                    const hash = b[1];

                    // UPDATE VERSION FILE
                    current_version = {
                        truth_version: truth_version,
                        hash: hash,
                    };
                    fs.writeFile(version_file, JSON.stringify(current_version), function (err) {
                        if (err) throw err;
                    });

                    // DOWNLOAD FILES
                    download_CDB(hash).then(() => {
                        download_manifest().then(() => {
                            // DATABASE UPDATE COMPLETE
                            resolve();
                        });
                    });
                });
            }).end();
        });

        function download_CDB(hash) {
            return new Promise(async function(resolve) {
                const cdb_path = path.join(database_dir, 'master.cdb');
                const db_path = path.join(database_dir, 'master.db');
                const file = fs.createWriteStream(cdb_path);
                http.get('http://prd-priconne-redive.akamaized.net/dl/pool/AssetBundles/' + hash.substr(0, 2) + '/' + hash, function(response) {
                    const stream = response.pipe(file);
                    stream.on('finish', () => {
                        // CONVERT CDB TO MDB/DB
                        exec('Coneshell_call.exe -cdb ' + cdb_path + ' ' + db_path, (error, stdout, stderr) => {
                            if (error) throw error;
                            if (stderr) throw stderr;
                            console.log('DOWNLOADED AND CONVERTED DATABASE [' + hash + '] ; SAVED AS ' + db_path);
                            resolve();
                        });
                    });
                });
            });
        }

        function download_single_manifest(manifest_name) {
            return new Promise(async function(resolve) {
                http.request({
                    host: 'prd-priconne-redive.akamaized.net',
                    path: '/dl/Resources/' + truth_version + '/Jpn/AssetBundles/Windows/manifest/' + manifest_name,
                    method: 'GET',
                }, (res) => {
                    let bundle = '';
                    res.on('data', function(chunk) {
                        bundle += Buffer.from(chunk).toString();
                    });
                    res.on('end', () => {
                        const manifest_path = path.join(database_dir, manifest_name);
                        fs.writeFile(manifest_path, bundle, function (err) {
                            if (err) throw err;
                            console.log('DOWNLOADED ' + manifest_name + ' ; SAVED AS', manifest_path);
                            resolve();
                        });
                    });
                }).end();
            });
        }

        function download_manifest() {
            return new Promise(async function(resolve) {
                let bundle = '';
                http.request({
                    host: 'prd-priconne-redive.akamaized.net',
                    path: '/dl/Resources/' + truth_version + '/Jpn/AssetBundles/Windows/manifest/icon_assetmanifest',
                    method: 'GET',
                }, (res) => {
                    res.on('data', function(chunk) {
                        bundle += Buffer.from(chunk).toString();
                    });
                    res.on('end', () => {
                        bundle += '\n';
                        http.request({
                            host: 'prd-priconne-redive.akamaized.net',
                            path: '/dl/Resources/' + truth_version + '/Jpn/AssetBundles/Windows/manifest/unit_assetmanifest',
                            method: 'GET',
                        }, (res) => {
                            res.on('data', function(chunk) {
                                bundle += Buffer.from(chunk).toString();
                            });
                            res.on('end', () => {
                                const manifest_path = path.join(database_dir, 'manifest');
                                fs.writeFile(manifest_path, bundle, function (err) {
                                    if (err) throw err;
                                    console.log('DOWNLOADED ICON/UNIT MANIFEST ; SAVED AS', manifest_path);
                                    resolve();
                                });
                            });
                        }).end();
                    });
                }).end();
            });
        }
    });
}

function create_spritesheets() {
    return new Promise(async (resolve) => {
        console.log('CREATING SPRITESHEETS');
        const pqh_dir = config["system"]["priconne-quest-helper_directory"],
            output_dir = config["system"]["output_directory"],
            setup_dir = config["system"]["setup_directory"],
            item_images_path = path.join(pqh_dir, 'images', 'items'),
            unit_icon_images_path = path.join(pqh_dir, 'images', 'unit_icon');
        // PREPARE DIRECTORIES
        bulk_create_directory(path.join(output_dir, 'css'));
        bulk_create_directory(path.join(output_dir, "images", "webpage", "spritesheets"));
        bulk_create_directory(path.join(output_dir, "images", "webpage_webp", "spritesheets"));

        // CREATE SPRITESHEETS
        fse.copySync(item_images_path, path.join(setup_dir, 'images'));
        await python_tools.create_spritesheet("item", css_path, path.join(setup_dir, "images"), output_dir);
        fse.copySync(unit_icon_images_path, path.join(setup_dir, 'images'));
        await python_tools.create_spritesheet("unit", css_path, path.join(setup_dir, "images"), output_dir);

        // DONE
        resolve();
    });
}

function get_new_images() {
    return new Promise (async (resolve) => {
        console.log('SEARCHING FOR NEW ITEMS...');
        let file_queue = [];

        // OPEN (LATEST CREATED) EQUIPMENT DATA AND TRANSLATE ME DOCUMENT
        const translate_path = path.join('.', config["system"]["setup_directory"], "translate_me.json"),
            equipment_path = path.join('.', config["system"]["output_directory"], "data", "equipment_data.json"),
            equipment_data = JSON.parse(fs.readFileSync(equipment_path, 'utf-8'));
        if (fs.existsSync(translate_path)) {
            const translate_data = JSON.parse(fs.readFileSync(translate_path, 'utf-8'));
            for (const key in translate_data) {
                // CHECK IF ITEM IS EQUIPMENT
                if (key.substring(0, 2) === config["equipment_dictionary"]["full_equipment"]) {
                    file_queue.push('equipment_' + key);
                    if (equipment_data[key]["has_fragments"]) {
                        file_queue.push('equipment_' + equipment_data[key]["fragment_id"]);
                    }
                }
                else if (key.substring(0, 2) === "31" || key.substring(0, 2) === "32") {
                    file_queue.push('item_' + key);
                }
            }
        }

        console.log('SEARCHING FOR NEW CHARACTERS...');
        let new_characters = {};
        const new_character_path = path.join('.', config["system"]["output_directory"], "data", "character_data.json"),
            old_character_path = path.join('.', config["system"]["setup_directory"], "character_data.json"),
            new_character = JSON.parse(fs.readFileSync(new_character_path, 'utf-8')),
            old_character = JSON.parse(fs.readFileSync(old_character_path, 'utf-8'));
        for (const char_key in new_character) {
            if (!old_character.hasOwnProperty(char_key)) {
                const unit_id = new_character[char_key]["unit_id"],
                    unit_3_id = unit_id.toString().substring(0, 4) + '3' + unit_id.toString().substring(5);
                file_queue.push('unit_' + unit_3_id);
                new_characters[unit_3_id] = char_key;
            }
        }

        // EXTRACT IF THERE ARE NEW FILES
        if (file_queue.length > 0) {
            console.log('FOUND', file_queue.length, 'NEW FILES! DOWNLOADING AND DECRYPTING THEM NOW...');
            // DOWNLOAD AND DECRYPT NEW IMAGES
            const files = await extract_images(file_queue);

            // COPY TO OUTPUT FOLDER
            let dir_path = config["system"]["output_directory"];
            if (!fs.existsSync(dir_path)) {
                fs.mkdirSync(dir_path);
            }
            dir_path = path.join(dir_path, 'images');
            if (!fs.existsSync(dir_path)) {
                fs.mkdirSync(dir_path);
            }
            if (!fs.existsSync(path.join('setup', 'images'))) {
                fs.mkdirSync(path.join('setup', 'images'));
            }
            for (const file_name in files) {
                const png_dir_path = path.join(dir_path, files[file_name]["type"]),
                    webp_dir_path = path.join(dir_path, files[file_name]["type"] + "_webp");
                if (!fs.existsSync(png_dir_path)) {
                    fs.mkdirSync(png_dir_path);
                }
                if (!fs.existsSync(webp_dir_path)) {
                    fs.mkdirSync(webp_dir_path);
                }
                fs.copyFileSync(files[file_name]["decrypted_path"], files[file_name]["output_png_path"]);
                console.log('COPYING TO OUTPUT FOLDER:', files[file_name]["decrypted_path"], '->', files[file_name]["output_png_path"]);
                fs.copyFileSync(files[file_name]['decrypted_path'], files[file_name]['setup_path']);
                console.log('COPYING TO SETUP FOLDER', files[file_name]["decrypted_path"], '->', files[file_name]["setup_path"]);
                convert_to_webp(files[file_name]["decrypted_path"], files[file_name]["output_webp_path"]);
            }
        }

        resolve();
    });
}

function extract_images(file_queue) {
    const equipment_data = JSON.parse(fs.readFileSync(path.join('.', config["system"]["output_directory"], "data", "equipment_data.json"), 'utf-8'));
    const character_data = JSON.parse(fs.readFileSync(path.join('.', config["system"]["output_directory"], "data", "character_data.json"), 'utf-8'));
    return new Promise(async (resolve) => {
        const directory = config["database"]["download_directory"],
            encrypted_dir = path.join(directory, 'encrypted'),
            decrypted_dir = path.join(directory, 'decrypted');

        // CREATE DIRECTORIES
        if (!fs.existsSync(directory)) {
            fs.mkdirSync(directory);
        }
        if (!fs.existsSync(encrypted_dir)) {
            fs.mkdirSync(encrypted_dir);
        }
        if (!fs.existsSync(decrypted_dir)) {
            fs.mkdirSync(decrypted_dir);
        }

        // FIND FILE HASH FROM MANIFEST
        const manifest_path = path.join(database_dir, 'manifest'),
            manifest = fs.readFileSync(manifest_path, 'utf8');
        let files = {};
        file_queue.forEach((file_name) => {
            const file_index = manifest.indexOf(file_name),
                line_end = manifest.indexOf('\n', file_index),
                file_data = manifest.substring(file_index, line_end).split(',');

            // FIGURE OUT DECRYPTED IMAGE NAME
            let id = file_name.split('_')[1];
            let output_name, type;
            if (file_name.includes('item') || file_name.includes('equipment')) {
                // FILE IS A MEMORY PIECE OR EQUIPMENT ICON ; DATA CAN BE FOUND ABOUT IT IN EQUIPMENT DATA
                type = "items";
                const item_type = id.substring(0, 2);
                if (item_type === "31" || item_type === "32" || item_type === "10") {
                    // FILE IS A MEMORY PIECE OR FULL EQUIPMENT, ID IS FINE AS IS
                    const item_name = equipment_data[id]["name"];
                    output_name = (item_name === "" ? file_name : item_name);
                }
                else if (item_type === "11" || item_type === "12") {
                    // FILE IS A EQUIPMENT FRAGMENT OR EQUIPMENT BLUEPRINT, MODIFY ID
                    const item_name = equipment_data["10" + id.slice(2)]["name"];
                    output_name = (item_name === "" ? file_name : item_name + " Fragment");
                }
            }
            else if (file_name.includes('unit')) {
                // FILE IS A UNIT ICON ; DATA CAN BE FOUND ABOUT IT IN CHARACTER DATA
                type = "unit_icon";
                id = id.substring(0, 4) + '0' + id.substring(5);
                for (const key in character_data) {
                    if (character_data[key]["unit_id"] === parseInt(id)) {
                        output_name = ((character_data[key]["thematic"] !== "") ? character_data[key]["thematic"] + " " : "") + character_data[key]["name"];
                        break;
                    }
                }
            }

            files[file_name] = {
                "hash": file_data[1],
                "type": type,
                "encrypted_path": path.join('.', extract_dir, 'encrypted', file_name + '.unity3d'),
                "decrypted_path": path.join('.', extract_dir, 'decrypted', output_name.split(' ').join('_') + '.png'),
                "output_png_path": path.join('.', config["system"]["output_directory"], 'images', type, output_name.split(' ').join('_') + '.png'),
                "output_webp_path": path.join('.', config["system"]["output_directory"], 'images', type + '_webp', output_name.split(' ').join('_') + '.webp'),
                "setup_path": path.join('.', config["system"]["setup_directory"], 'images', output_name.split(' ').join('_') + '.png')
            };
        });

        // DOWNLOAD ENCRYPTED .unity3d FILES FROM CDN
        for (const file_name in files) {
            await get_asset(files[file_name]["encrypted_path"], files[file_name]["hash"]);
            console.log('DOWNLOADED', file_name , '; SAVED AS', files[file_name]["encrypted_path"]);
            await python_tools.deserialize(files[file_name]["encrypted_path"], files[file_name]["decrypted_path"]);
        }

        resolve(files);
    });

    function get_asset(output_path, hash) {
        return new Promise(async function(resolve) {
            const file = fs.createWriteStream(output_path);
            http.get('http://prd-priconne-redive.akamaized.net/dl/pool/AssetBundles/' + hash.substr(0, 2) + '/' + hash, function(response) {
                const stream = response.pipe(file);
                stream.on('finish', () => {
                    resolve();
                });
            });
        });
    }
}

function confirm_empty_directory(directory) {
    if (!fs.existsSync(directory)) {
        fs.mkdirSync(directory);
        console.log('CREATED DIRECTORY', directory);
    }
    else {
        clean_directory(directory);
        console.log('CLEANED DIRECTORY', directory);
    }
}

function clean_directory(directory) {
    const files = fs.readdirSync(directory);
    for (const file of files) {
        if (fs.statSync(path.join(directory, file)).isDirectory()) {
            clean_directory(path.join(directory, file));
            fs.rmdirSync(path.join(directory, file));
        }
        else {
            fs.unlinkSync(path.join(directory, file));
        }
    }
}

function bulk_create_directory(dest) {
    const directories = dest.split('\\');
    let current_path = "";
    directories.forEach((dir) => {
        if (dir.indexOf('.') !== -1) {
            return;
        }
        current_path = path.join(current_path, dir);
        if (!fs.existsSync(current_path)) {
            fs.mkdirSync(current_path);
        }
    });
}

function convert_to_webp(input_path, output_path) {
    webp.cwebp(input_path, output_path, "-q 70");
}

function write_equipment_data() {
    return new Promise(async (resolve) => {
        let counters = {
            "common": 1,
            "copper": 1,
            "silver": 1,
            "gold": 1,
            "purple": 1,
            "red": 1,
            "misc": 1
        };
        let db, result, data = {};

        // OPEN DATABASE
        db = await open({
            filename: path.join('.', database_dir, 'master.db'),
            driver: sqlite3.Database
        });
        result = await db.all('SELECT equipment_id, equipment_name FROM equipment_data');
        result.forEach((entry) => {
            const full_id = entry["equipment_id"],
                item_id = get_item_id(full_id),
                item_type = get_item_type(full_id);
            if (item_type === equipment_dictionary['full_equipment']) {
                const rarity_string = rarity_id_to_rarity_string(get_rarity_id(full_id));
                data[full_id.toString()] = {
                    "name_jp": entry["equipment_name"],
                    "name": "",
                    "id": rarity_string + '-' + counters[rarity_string],
                    "has_fragments": false,
                    "fragment_id": "",
                    "req_pieces": 1,
                    "req_items": []
                };
                counters[rarity_string]++;
            }
            else {
                const is_fragment = item_type === equipment_dictionary['equipment_fragment'],
                    is_blueprint = item_type === equipment_dictionary['equipment_blueprint'];
                if (is_fragment || is_blueprint) {
                    data[equipment_dictionary['full_equipment'] + item_id]["has_fragments"] = true;
                    data[equipment_dictionary['full_equipment'] + item_id]["fragment_id"] = full_id.toString();
                }
            }
        });

        // GET CHARACTER MEMORY PIECES AVAILABLE FROM HARD AND VERY HARD QUESTS
        let memory_piece_whitelist = [];
        result = await db.all('SELECT quest_id, reward_image_1 FROM quest_data');
        result.forEach((entry) => {
            const quest_id = entry["quest_id"],
                quest_type = quest_id.toString().substring(0, 2);
            if (quest_type === quest_dictionary["hard_difficulty"] ||
                quest_type === quest_dictionary["very_hard_difficulty"]) {
                if (entry["reward_image_1"] !== 0) {
                    memory_piece_whitelist.push(entry["reward_image_1"]);
                }
            }
        });

        // ADD CHARACTER MEMORY PIECES;
        result = await db.all('SELECT item_id, item_name, item_type FROM item_data');
        result.forEach((entry) => {
            if (entry["item_type"] === 11 || entry["item_type"] === 18) {
                let item_id = entry["item_id"];
                if (memory_piece_whitelist.includes(item_id)) {
                    data[item_id.toString()] = {
                        "name_jp": entry["item_name"].toString(),
                        "name": "",
                        "id": "misc-" + counters["misc"],
                        "has_fragments": false,
                        "fragment_id": "",
                        "req_pieces": 1,
                        "req_items": []
                    };
                    counters["misc"]++;
                }
            }
        });

        const old_equipment_data = JSON.parse(fs.readFileSync(path.join('.', config["system"]["setup_directory"], "equipment_data.json"), 'utf-8'));
        // ADD CURRENT ENGLISH TRANSLATION FROM OLD EQUIPMENT FILE
        for (const key in old_equipment_data) {
            data[key]["name"] = old_equipment_data[key]["name"];
        }

        // CHECK IF NEW ITEMS EXIST
        if (Object.keys(data).length > Object.keys(old_equipment_data).length) {
            // NEW ITEMS EXIST, DETERMINE WHAT NEEDS TO BE TRANSLATED
            let needs_translation = {};
            for (const key in data) {
                if (data[key]["name"] === "") {
                    needs_translation[key] = {
                        "name_jp": data[key]["name_jp"],
                        "en_translation": ""
                    };
                }
            }

            const translate_path = path.join(config["system"]["setup_directory"], 'translate_me.json');
            fs.writeFile(translate_path, JSON.stringify(needs_translation, null, 4), function(err) {
                if (err) throw err;
            });

            await sendQuestion(translate_path + " has been created. Translate the items and press ENTER to continue...");

            const translation = JSON.parse(fs.readFileSync(translate_path, 'utf-8'));
            for (const key in translation) {
                data[key]["name"] = translation[key]["en_translation"];
            }
        }

        // ADD REQUIRED FRAGMENTS
        result = await db.all('SELECT equipment_id, condition_equipment_id_1, consume_num_1 FROM equipment_craft');
        result.forEach((entry) => {
            const equip_id = entry["equipment_id"];
            if (get_item_type(equip_id) === equipment_dictionary["full_equipment"]) {
                // CHECK IF condition_equipment_id_1 IS THE SAME AS EQUIPMENT ID
                if (get_item_id(equip_id) === get_item_id(entry["condition_equipment_id_1"])) {
                    data[equip_id.toString()]["req_pieces"] = entry["consume_num_1"];
                }
                else {
                    // IF condition_equipment_id_1 DOES NOT MATCH EQUIPMENT ID, MEANS THERE ARE NO FRAGMENTS
                    // SET condition_equipment_id_1 AS A REQUIRED ITEM INSTEAD
                    // THIS IS MAINLY USED FOR THE ITEM Sorcerer's Glasses
                    data[equip_id.toString()]["req_pieces"] = 0;
                    let req_items_array = data[equip_id.toString()]["req_items"],
                        req_item_name = data[entry["condition_equipment_id_1"].toString()]["name"];
                    req_items_array.push(req_item_name);
                    data[equip_id.toString()]["req_items"] = req_items_array;
                }
            }
        });

        // ADD REQUIRED ITEMS
        result = await db.all('SELECT equipment_id, condition_equipment_id_2, condition_equipment_id_3, condition_equipment_id_4 FROM equipment_craft');
        result.forEach((entry) => {
            const equip_id = entry["equipment_id"],
                cond_2 = entry["condition_equipment_id_2"],
                cond_3 = entry["condition_equipment_id_3"],
                cond_4 = entry["condition_equipment_id_4"];
            if (get_item_type(equip_id) === equipment_dictionary["full_equipment"]) {
                let req_items_array = data[equip_id.toString()]["req_items"];

                // CONDITION EQUIPMENT 2
                if (cond_2 !== 0) {
                    req_items_array.push(data[cond_2.toString()]["name"]);
                }

                // CONDITION EQUIPMENT 3
                if (cond_3 !== 0) {
                    req_items_array.push(data[cond_3.toString()]["name"]);
                }

                // CONDITION EQUIPMENT 4
                if (cond_4 !== 0) {
                    req_items_array.push(data[cond_4.toString()]["name"]);
                }

                // ADD REQUIRED ITEMS BACK TO DATA
                data[equip_id.toString()]["req_items"] = req_items_array;
            }
        });

        // EQUIPMENT DATA WRITE COMPLETE ; SAVE FILE
        const output_data_dir = path.join(config["system"]["output_directory"], "data"),
            equipment_data_path = path.join(output_data_dir, 'equipment_data.json');
        if (!fs.existsSync(output_data_dir)) {
            fs.mkdirSync(output_data_dir);
        }
        fs.writeFile(equipment_data_path, JSON.stringify(data, null, 4), async function(err) {
            if (err) throw err;
            await python_tools.fix_equipment_data(equipment_data_path);
            console.log('CREATED EQUIPMENT DATA ; SAVED AS', equipment_data_path);
            db.close().finally(() => {
                resolve();
            });
        });
    });

    function get_item_type(full_id) {
        return full_id.toString().substring(0, 2);
    }

    function get_rarity_id(full_id) {
        return full_id.toString().substring(2, 3);
    }

    function get_item_id(full_id) {
        return full_id.toString().substring(2);
    }

    function rarity_id_to_rarity_string(rarity_id) {
        return equipment_dictionary['rarity-' + rarity_id];
    }

    function sendQuestion(query) {
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
        });

        return new Promise(resolve => rl.question(query, (answer) => {
            rl.close();
            process.stdin.destroy();
            resolve(answer);
        }))
    }
}

function write_character_data() {
    return new Promise(async function(resolve) {
        let db, result, data = {};

        // OPEN DATABASE
        db = await open({
            filename: path.join('.', database_dir, 'master.db'),
            driver: sqlite3.Database
        });

        // OPEN (LATEST CREATED) EQUIPMENT DATA
        const equipment_data = JSON.parse(fs.readFileSync(path.join('.', config["system"]["output_directory"], "data", "equipment_data.json"), 'utf-8'));

        let name_jp_to_en_dictionary = {}, thematic_jp_to_en_dictionary = {};
        const jp_data = JSON.parse(fs.readFileSync(path.join('.', config["system"]["setup_directory"], "ja-JP.json"), 'utf-8'));

        // BUILD CHARACTER NAME (JP) -> EN
        const character_name_data = jp_data["character_names"];
        for (const key in character_name_data) {
            name_jp_to_en_dictionary[character_name_data[key]] = key;
        }

        // BUILD THEMATIC (JP) -> EN
        const thematic_data = jp_data["thematics"];
        for (const key in thematic_data) {
            thematic_jp_to_en_dictionary[thematic_data[key]] = key;
        }

        // CREATE UNIT DATA DICTIONARY
        let unit_data_to_unit_name = {};
        result = await db.all('SELECT unit_id, unit_name FROM unit_data');
        result.forEach((entry) => {
            const unit_id = entry["unit_id"];
            // UNIT ID ABOVE 190,000 ARE NPCS OR STORY UNITS
            if (unit_id < 190000) {
                unit_data_to_unit_name[unit_id] = entry["unit_name"];
            }
        });

        // GET UNIT PROMOTION REQUIREMENTS
        result = await db.all('SELECT unit_id, promotion_level, equip_slot_1, equip_slot_2, equip_slot_3, ' +
            'equip_slot_4, equip_slot_5, equip_slot_6 FROM unit_promotion');
        result.forEach((entry) => {
            // unit_id ABOVE 400,000 ARE NPCS OR STORY UNITS
            // CHECK EVERYTHING BELOW 190,000 REGARDLESS TO MATCH UNIT DATA DICTIONARY
            const unit_id = entry["unit_id"];
            if (unit_id < 190000) {
                let unit_key, name_en, thematic_en = "", name_jp, thematic_jp = "";
                const full_unit_name = unit_data_to_unit_name[unit_id],
                    promotion_level = entry["promotion_level"],
                    es_1 = entry["equip_slot_1"],
                    es_2 = entry["equip_slot_2"],
                    es_3 = entry["equip_slot_3"],
                    es_4 = entry["equip_slot_4"],
                    es_5 = entry["equip_slot_5"],
                    es_6 = entry["equip_slot_6"],
                    equip_slot_1 = (es_1 !== 999999) ? equipment_data[es_1.toString()]["name"] : "",
                    equip_slot_2 = (es_2 !== 999999) ? equipment_data[es_2.toString()]["name"] : "",
                    equip_slot_3 = (es_3 !== 999999) ? equipment_data[es_3.toString()]["name"] : "",
                    equip_slot_4 = (es_4 !== 999999) ? equipment_data[es_4.toString()]["name"] : "",
                    equip_slot_5 = (es_5 !== 999999) ? equipment_data[es_5.toString()]["name"] : "",
                    equip_slot_6 = (es_6 !== 999999) ? equipment_data[es_6.toString()]["name"] : "";

                if (full_unit_name === undefined) {
                    console.log('undefined', unit_id);
                }
                else {
                    // GET UNIT KEY / NAME_EN / THEMATIC_EN / NAME_JP / THEMATIC_JP
                    if (full_unit_name.indexOf("（") > -1) {
                        // PARENTHESIS EXISTS... MEANS THERE'S PROBABLY A THEMATIC
                        let parenthesis_index = full_unit_name.indexOf("（");
                        thematic_jp = full_unit_name.substring(parenthesis_index + 1, full_unit_name.length - 1);
                        thematic_en = thematic_jp_to_en_dictionary[thematic_jp];
                        name_jp = full_unit_name.substring(0, parenthesis_index);
                        name_en = name_jp_to_en_dictionary[name_jp];
                        unit_key = thematic_en + '_' + name_en;

                        // CAPITALIZE name_en AND thematic_en
                        name_en = name_en.charAt(0).toUpperCase() + name_en.slice(1);
                        if (thematic_en.indexOf('_') === -1) {
                            thematic_en = thematic_en.charAt(0).toUpperCase() + thematic_en.slice(1);
                        }
                        else {
                            let split_thematic = thematic_en.split('_');
                            thematic_en = "";
                            split_thematic.forEach((thematic_part) => {
                                thematic_en += thematic_part.charAt(0).toUpperCase() + thematic_part.slice(1) + " ";
                            });
                            // REMOVE THE LAST (UNNECESSARY) SPACE
                            thematic_en = thematic_en.substring(0, thematic_en.length - 1);
                        }
                    }
                    else {
                        // NO PARENTHESIS. JUST BASIC UNIT NAME
                        unit_key = name_jp_to_en_dictionary[full_unit_name];
                        name_en = unit_key.charAt(0).toUpperCase() + unit_key.slice(1);
                        name_jp = full_unit_name;
                    }

                    // INSERT UNIT DATA (IF IT DOESN'T ALREADY EXIST)
                    if (!data.hasOwnProperty(unit_key)) {
                        data[unit_key] = {
                            "unit_id": unit_id,
                            "name": name_en,
                            "thematic": thematic_en,
                            "name_jp": name_jp,
                            "thematic_jp": thematic_jp
                        };
                    }
                    // INSERT RANK EQUIPMENT
                    data[unit_key]["rank_" + promotion_level] = [equip_slot_1, equip_slot_2, equip_slot_3, equip_slot_4, equip_slot_5, equip_slot_6];
                }
            }
        });

        // SORT DICTIONARY ALPHABETICALLY
        let sorted_character_names = [], characters_with_thematics = {};
        Object.keys(data).forEach((key) => {
            if (key.indexOf('_') === -1) {
                // NO '_' MEANS NO THEMATIC
                sorted_character_names.push(key);
            }
            else {
                // THEMATIC FOUND, ADD TO LIST AND SORT
                const character_name = key.substring(key.lastIndexOf('_') + 1, key.length);
                if (!characters_with_thematics.hasOwnProperty(character_name)) {
                    characters_with_thematics[character_name] = [];
                }
                characters_with_thematics[character_name].push(key);

                // CHECK IF THERE IS A BASE VERSION OF THE CHARACTER, IF NOT THEN ADD ONE
                // THIS IS TO DEAL WITH CHARACTERS LIKE 'Mio (Deresute)' and 'Uzuki (Deresute)'
                if (!sorted_character_names.includes(character_name)) {
                    sorted_character_names.push(character_name);
                }
            }
        });

        let sorted_data = {};
        sorted_character_names.sort().forEach((key) => {
            if (data.hasOwnProperty(key)) {
                // BASE VERSION EXISTS
                sorted_data[key] = data[key];
            }

            if (characters_with_thematics.hasOwnProperty(key)) {
                // CHARACTER HAS AN ALTERNATE VERSION
                // ADD ALTERNATE VERSION AFTER BASE VERSION
                characters_with_thematics[key].sort().forEach((thematic) => {
                    sorted_data[thematic] = data[thematic];
                })
            }
        });
        data = sorted_data;

        // CHARACTER DATA WRITE COMPLETE ; SAVE FILE
        const output_data_dir = path.join(config["system"]["output_directory"], "data");
        if (!fs.existsSync(output_data_dir)) {
            fs.mkdirSync(output_data_dir);
        }
        fs.writeFile(path.join(output_data_dir, 'character_data.json'), JSON.stringify(data, null, 4), function(err) {
            if (err) throw err;
            console.log('CREATED CHARACTER DATA ; SAVED AS', path.join(output_data_dir, 'character_data.json'));
            db.close().finally(() => {
                resolve();
            });
        });
    });
}

function write_quest_data() {
    let wave_group_info, enemy_reward_info;

    // OPEN (LATEST CREATED) EQUIPMENT DATA
    const equipment_data = JSON.parse(fs.readFileSync(path.join('.', config["system"]["output_directory"], "data", "equipment_data.json"), 'utf-8'));
    return new Promise(async function(resolve) {
        let db, result, data = {}, quest_data = {};

        // OPEN DATABASE
        db = await open({
            filename: path.join('.', database_dir, 'master.db'),
            driver: sqlite3.Database
        });

        result = await db.all('SELECT quest_id, quest_name, wave_group_id_1, wave_group_id_2, wave_group_id_3 FROM quest_data');
        result.forEach((entry) => {
            const quest_id = entry["quest_id"];
            let quest_type = quest_id.toString().substring(0, 2);
            if (parseInt(quest_type) !== 18 && parseInt(quest_type) !== 19) {
                const quest_full_name = entry["quest_name"],
                    quest_chapter = quest_full_name.substring(quest_full_name.indexOf(' ') + 1, quest_full_name.indexOf('-')),
                    quest_number = quest_full_name.substring(quest_full_name.indexOf('-') + 1);
                let quest_difficulty;
                if (quest_type === quest_dictionary["normal_difficulty"]) {
                    quest_type = "";
                    quest_difficulty = "NORMAL";
                }
                else if (quest_type === quest_dictionary["hard_difficulty"]) {
                    quest_type = "H";
                    quest_difficulty = "HARD";
                }
                else if (quest_type === quest_dictionary["very_hard_difficulty"]) {
                    quest_type = "VH";
                    quest_difficulty = "VERY HARD";
                }
                else {
                    console.log('UNKNOWN QUEST TYPE!', quest_full_name, quest_type);
                    quest_type = "???";
                    quest_difficulty = "UNKNOWN";
                }
                quest_data[quest_id.toString()] = {
                    "id": quest_id,
                    "name": quest_full_name,
                    "key": quest_chapter + '-' + quest_number + quest_type,
                    "difficulty": quest_difficulty,
                    "wave_group_id_1": entry["wave_group_id_1"],
                    "wave_group_id_2": entry["wave_group_id_2"],
                    "wave_group_id_3": entry["wave_group_id_3"]
                };
            }
        });

        // COLLECT wave_group_data INFORMATION
        let wave_group_data = {};
        result = await db.all('SELECT wave_group_id, drop_reward_id_1, drop_reward_id_2, drop_reward_id_3, ' +
            'drop_reward_id_4, drop_reward_id_5 FROM wave_group_data');
        result.forEach((entry) => {
            wave_group_data[entry["wave_group_id"]] = {
                "wave_group_id": entry["wave_group_id"],
                "drop_reward_1": entry["drop_reward_id_1"],
                "drop_reward_2": entry["drop_reward_id_2"],
                "drop_reward_3": entry["drop_reward_id_3"],
                "drop_reward_4": entry["drop_reward_id_4"],
                "drop_reward_5": entry["drop_reward_id_5"],
            };
        });
        wave_group_info = wave_group_data;

        // COLLECT enemy_reward_data INFORMATION
        let enemy_reward_data = {};
        result = await db.all('SELECT drop_reward_id, reward_type_1, reward_id_1, odds_1, ' +
            'reward_type_2, reward_id_2, odds_2, ' +
            'reward_type_3, reward_id_3, odds_3, ' +
            'reward_type_4, reward_id_4, odds_4, ' +
            'reward_type_5, reward_id_5, odds_5 FROM enemy_reward_data');
        result.forEach((entry) => {
            enemy_reward_data[entry["drop_reward_id"]] = {
                "drop_reward_id": entry["drop_reward_id"],
                "reward_type_1": entry["reward_type_1"],
                "reward_id_1": entry["reward_id_1"],
                "reward_odds_1": entry["odds_1"],

                "reward_type_2": entry["reward_type_2"],
                "reward_id_2": entry["reward_id_2"],
                "reward_odds_2": entry["odds_2"],

                "reward_type_3": entry["reward_type_3"],
                "reward_id_3": entry["reward_id_3"],
                "reward_odds_3": entry["odds_3"],

                "reward_type_4": entry["reward_type_4"],
                "reward_id_4": entry["reward_id_4"],
                "reward_odds_4": entry["odds_4"],

                "reward_type_5": entry["reward_type_5"],
                "reward_id_5": entry["reward_id_5"],
                "reward_odds_5": entry["odds_5"],
            };
        });
        enemy_reward_info = enemy_reward_data;

        // BUILD QUEST DATA JSON
        for (const key in quest_data) {
            let quest = quest_data[key];

            // CHECK IF QUEST HAS ALL WAVE DATA
            if (quest["wave_group_id_1"] !== 0 &&
                quest["wave_group_id_2"] !== 0 &&
                quest["wave_group_id_3"] !== 0) {

                // GET QUEST DROPS
                if (quest['difficulty'] === 'NORMAL') {
                    data = add_quest_entry(data, quest);

                    // CHECK IF ANY MORE NORMAL QUESTS
                    const quest_id = quest["id"].toString(),
                        quest_number = quest_id.substring(quest_id.length - 3),
                        quest_chapter = quest_id.substring(quest_id.length - 6, quest_id.length - 3),
                        next_quest_number = (parseInt(quest_number) + 1).toString().padStart(3, '0'),
                        next_quest_id = "11" + quest_chapter + next_quest_number;
                    if (!quest_data.hasOwnProperty(next_quest_id)) {
                        // ADD HARD QUESTS
                        let hard_quest_counter = 1,
                            hard_quest_id = "12" + quest_chapter + hard_quest_counter.toString().padStart(3, '0');
                        while (quest_data.hasOwnProperty(hard_quest_id)) {
                            quest = quest_data[hard_quest_id];
                            if (quest["wave_group_id_1"] !== 0 &&
                                quest["wave_group_id_2"] !== 0 &&
                                quest["wave_group_id_3"] !== 0) {
                                data = add_quest_entry(data, quest);
                            }
                            hard_quest_counter++;
                            hard_quest_id = "12" + quest_chapter + hard_quest_counter.toString().padStart(3, '0');
                        }

                        // ADD VERY HARD QUESTS
                        hard_quest_counter = 1;
                        hard_quest_id = '13' + quest_chapter + hard_quest_counter.toString().padStart(3, '0');
                        while (quest_data.hasOwnProperty(hard_quest_id)) {
                            quest = quest_data[hard_quest_id];
                            if (quest["wave_group_id_1"] !== 0 &&
                                quest["wave_group_id_2"] !== 0 &&
                                quest["wave_group_id_3"] !== 0) {
                                data = add_quest_entry(data, quest);
                            }
                            hard_quest_counter++;
                            hard_quest_id = "13" + quest_chapter + hard_quest_counter.toString().padStart(3, '0');
                        }
                    }
                }
            }
        }

        // QUEST DATA WRITE COMPLETE ; SAVE FILE
        const output_data_dir = path.join(config["system"]["output_directory"], "data");
        if (!fs.existsSync(output_data_dir)) {
            fs.mkdirSync(output_data_dir);
        }
        fs.writeFile(path.join(output_data_dir, 'quest_data.json'), JSON.stringify(data, null, 4), function(err) {
            if (err) throw err;
            console.log('CREATED QUEST DATA ; SAVED AS', path.join(output_data_dir, 'quest_data.json'));
            db.close().finally(() => {
                resolve();
            });
        });
    });

    function get_next_key(data) {
        let counter = 1;
        while (data.hasOwnProperty('item_' + counter)) {
            counter++;
        }
        return 'item_' + counter;
    }

    function get_quest_drops(data, wave_group) {
        let drop_reward_counter = 1;
        while (drop_reward_counter <= 5) {
            // GET WAVE DROPS
            const wave_drops = wave_group['drop_reward_' + drop_reward_counter];
            if (wave_drops !== 0) {
                // GET ITEMS FROM WAVE DROPS
                const enemy_reward = enemy_reward_info[wave_drops];

                // CHECK IF WAVE GIVES SUBDROPS
                if (enemy_reward["reward_id_1"] !== 0 &&
                    enemy_reward["reward_id_2"] !== 0 &&
                    enemy_reward["reward_id_3"] !== 0 &&
                    enemy_reward["reward_id_4"] !== 0 &&
                    enemy_reward["reward_id_5"] !== 0) {
                    data["subdrops"] = [
                        {
                            "reward_id": enemy_reward["reward_id_1"],
                            "reward_odds": enemy_reward["reward_odds_1"],
                        },
                        {
                            "reward_id": enemy_reward["reward_id_2"],
                            "reward_odds": enemy_reward["reward_odds_2"],
                        },
                        {
                            "reward_id": enemy_reward["reward_id_3"],
                            "reward_odds": enemy_reward["reward_odds_3"],
                        },
                        {
                            "reward_id": enemy_reward["reward_id_4"],
                            "reward_odds": enemy_reward["reward_odds_4"],
                        },
                        {
                            "reward_id": enemy_reward["reward_id_5"],
                            "reward_odds": enemy_reward["reward_odds_5"],
                        }
                    ];
                }
                else {
                    let enemy_reward_counter = 1;
                    while (enemy_reward_counter <= 5) {
                        const reward_type = enemy_reward["reward_type_" + enemy_reward_counter],
                            reward_id = enemy_reward["reward_id_" + enemy_reward_counter],
                            reward_odds = enemy_reward["reward_odds_" + enemy_reward_counter],
                            item = {
                                "reward_id": reward_id,
                                "reward_odds": reward_odds
                            };
                        if (reward_id !== 0) {
                            // IF DROP IS EQUIPMENT
                            if (reward_type === 4) {
                                const key = get_next_key(data);
                                data[key] = item;
                            }
                            else {
                                if (reward_type === 2) {
                                    // CHECK IF ITEM IS A MEMORY PIECE
                                    if (reward_id.toString().substring(0, 1) === '3') {
                                        data['char_shard'] = item;
                                    }
                                }
                            }
                        }
                        else {
                            break;
                        }
                        enemy_reward_counter++;
                    }
                }
            }
            else {
                drop_reward_counter++;
                continue;
            }
            drop_reward_counter++;
        }
        return data;
    }

    function add_quest_entry(data, quest) {
        // GET QUEST DROPS
        let quest_drops = get_quest_drops({}, wave_group_info[quest["wave_group_id_1"]]);
        quest_drops = get_quest_drops(quest_drops, wave_group_info[quest["wave_group_id_2"]]);
        quest_drops = get_quest_drops(quest_drops, wave_group_info[quest["wave_group_id_3"]]);

        // INIT QUEST ENTRY
        const quest_key = quest['key'];
        data[quest_key] = {
            "name": quest['name']
        };

        // ADD ITEMS 1 - 4
        let counter = 1;
        while (counter <= 4) {
            if (quest_drops.hasOwnProperty("item_" + counter)) {
                const item_id = quest_drops["item_" + counter]["reward_id"].toString().substring(2),
                    drop_percent = quest_drops["item_" + counter]["reward_odds"];
                let item_name = equipment_data["10" + item_id]["name"];

                // ADD ' Fragment' IF ITEM HAS FRAGMENTS
                if (equipment_data['10' + item_id]["has_fragments"]) {
                    item_name += " Fragment";
                }

                // ADD TO DATA
                data[quest_key]["item_" + counter] = {
                    "item_name": item_name,
                    "drop_percent": drop_percent
                }
            }
            counter++;
        }

        // ADD CHARACTER SHARD
        if (quest_drops.hasOwnProperty('char_shard')) {
            const item_id = quest_drops["char_shard"]["reward_id"].toString(),
                item_name = equipment_data[item_id]["name"];
            data[quest_key]["char_shard"] = {
                "item_name": item_name,
                "drop_percent": quest_drops["char_shard"]["reward_odds"]
            };
        }

        // ADD SUBDROPS AND DROP PERCENT
        let subdrops = [],
            subdrops_percent = [],
            subdrops_not_equal;
        quest_drops["subdrops"].forEach((item_data) => {
            const item_id = item_data["reward_id"].toString().substring(2),
                drop_percent = item_data["reward_odds"];
            let item_name = equipment_data["10" + item_id]["name"];

            // ADD " Fragment" IF ITEM HAS FRAGMENTS
            if (equipment_data["10" + item_id]["has_fragments"]) {
                item_name += " Fragment";
            }

            subdrops.push(item_name);
            subdrops_percent.push(drop_percent);
            subdrops_not_equal = subdrops_percent[0] !== drop_percent;
        });
        data[quest_key]["subdrops"] = subdrops;
        if (subdrops_not_equal) {
            data[quest_key]["subdrops_percent"] = subdrops_percent;
        }

        return data;
    }
}

function update_dictionary() {
    const equipment_data = JSON.parse(fs.readFileSync(path.join('.', config["system"]["output_directory"], "data", "equipment_data.json"), 'utf-8'));
    const dictionary = JSON.parse(fs.readFileSync(path.join('.', config["system"]["setup_directory"], "dictionary.json"), 'utf-8'));
    const dictionary_entry = {
        "ja-JP": "",
        "en-US": "",
        "ko-KR": "",
        "zh-CN": "",
        "is_fragment": false
    };
    console.log('UPDATING dictionary.json...');
    for (const key in equipment_data) {
        if (!dictionary["equipment"].hasOwnProperty(key)) {
            console.log("MISSING DICTIONARY ENTRY FOUND:", key);
            dictionary_entry["ja-JP"] = equipment_data[key]["name_jp"];
            dictionary_entry["en-US"] = equipment_data[key]["name"];
            dictionary_entry["is_fragment"] = (equipment_data[key]["fragment_id"].substring(0, 2) === config.equipment_dictionary.equipment_fragment);
            dictionary["equipment"][key] = clone_object(dictionary_entry);
        }
    }

    // SAVE FILE
    const output_path = path.join(config["system"]["output_directory"], "data", "dictionary.json");
    fs.writeFile(output_path, JSON.stringify(dictionary, null, 4), async function(err) {
        if (err) throw err;
        console.log('DICTIONARY UPDATE COMPLETE ; SAVED AS', output_path);
    });

    function clone_object(object) {
        return Object.assign({}, object);
    }
}