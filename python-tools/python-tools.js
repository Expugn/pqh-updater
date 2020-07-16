/**
 * UTILIZES python-tools/deserialize.py TO CONVERT A GIVEN .unity3d Texture2D FILE TO .png
 * READ THE COMMENTS OF deserialize.py TO SEE THE REQUIRED DEPENDENCIES
 *
 * @param {string}    import_path    PATH OF .unity3d FILE
 * @param {string}    export_path    PATH TO EXPORT THE .png FILE TO
 * @return {Promise<any>}
 */
function deserialize_unity3d(import_path, export_path) {
    const py_file = 'python-tools/deserialize.py',
        options = { args: [import_path, export_path] };
    return run_python(py_file, options);
}

/**
 * UTILIZES python-tools/fix-equipment-data.py TO "FIX" EQUIPMENT DATA ORDERING.
 * READS THE equipment_data.json PROVIDED AND MOVES ALL misc RARITY OBJECTS BACK TO THE BOTTOM AND OVERWRITES THE FILE.
 *
 * WHY?
 * node.js FOR SOME REASON MODIFIES THE ORDER OF NUMERICAL OBJECT KEYS (EVEN IF THEY'RE STRINGS).
 * THIS MEANS THAT misc RARITY (USUALLY MEMORY PIECES) WILL BE PLACED ON THE TOP
 * OF THE equipment_data.json FILE.
 * THIS DOESN'T REALLY FIX ANYTHING CODE-WISE, I GUESS, BUT IT'S NICER TO RETAIN THE SAME ORDER.
 *
 * @param {string}    import_path    PATH OF THE equipment_data.json FILE TO FIX AND OVERWRITE
 * @return {Promise<any>}
 */
function fix_equipment_data(import_path) {
    const py_file = 'python-tools/fix-equipment-data.py',
        options = { args: [import_path] };
    return run_python(py_file, options, true);
}

/**
 * UTILIZES python-tools/create-spritesheet.py TO CREATE A SPRITESHEET AND A CSS FILE.
 *
 * WHY?
 * BECAUSE THE CURRENT IMAGE PROCESSING OPTIONS I LOOKED UP FOR node.js ARE PRETTY LIMITED, I THINK. I'M MORE
 * COMFORTABLE WITH USING Pillow TO PROCESS THE IMAGES (ALSO I ALREADY WROTE THE CODE ON THE OLD pqh-updater LOL)
 *
 * @param {string}    type                     USE item FOR ITEM SPRITESHEET | USE unit FOR UNIT SPRITESHEET ; ITEM SPRITESHEET MUST BE CREATED BEFORE UNIT SPRITESHEET
 * @param {string}    css_path                 PATH TO THE CSS FILE TO BE CREATED
 * @param {string}    setup_image_directory    DIRECTORY CONTAINING ALL ITEM OR UNIT IMAGES THE SCRIPT CAN USE
 * @param {string}    output_directory         DIRECTORY WHERE FILES ARE OUTPUT FROM pqh-updater
 * @return {Promise<any>}
 */
function create_spritesheet(type, css_path, setup_image_directory, output_directory) {
    const py_file = 'python-tools/create-spritesheet.py',
        options = { args: [type, css_path, setup_image_directory, output_directory] };
    return run_python(py_file, options, true);
}

/**
 * RUN A PYTHON FILE USING python-shell
 *
 * @param {string}     py_file    PATH TO THE PYTHON FILE TO RUN
 * @param {object}     options    PARAMETERS TO USE WITH THE PYTHON FILE
 * @param {boolean}    silent     TRUE IF PYTHON CONSOLE OUTPUT MUST NOT BE DISPLAYED
 * @return {Promise<any>}
 */
function run_python(py_file, options, silent = false) {
    return new Promise(async function(resolve) {
        const { PythonShell } = require('python-shell');
        await PythonShell.run(py_file, options, function(err, results) {
            if (err) throw err;
            if (!silent) {
                for (let i of results) {
                    console.log('[' + py_file + ']', i);
                }
            }
            resolve();
        });
    });
}

module.exports.deserialize = deserialize_unity3d;
module.exports.fix_equipment_data = fix_equipment_data;
module.exports.create_spritesheet = create_spritesheet;