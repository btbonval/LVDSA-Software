// ==UserScript==
// @name         Volunteer Signup Spreadsheet to LVDSA
// @namespace    https://raw.githubusercontent.com/btbonval/LVDSA-Software/
// @version      2026-05-06
// @description  Reads Google Spreadsheet data, pushes entries into the correct LVDSA form.
// @homepage     https://raw.githubusercontent.com/btbonval/LVDSA-Software/refs/heads/main/tampermonkey/Volunteer%20Signup%20Spreadsheet%20to%20LVDSA.user.js
// @homepageURL  https://raw.githubusercontent.com/btbonval/LVDSA-Software/refs/heads/main/tampermonkey/Volunteer%20Signup%20Spreadsheet%20to%20LVDSA.user.js
// @website      https://raw.githubusercontent.com/btbonval/LVDSA-Software/refs/heads/main/tampermonkey/Volunteer%20Signup%20Spreadsheet%20to%20LVDSA.user.js
// @source       https://raw.githubusercontent.com/btbonval/LVDSA-Software/refs/heads/main/tampermonkey/Volunteer%20Signup%20Spreadsheet%20to%20LVDSA.user.js
// @updateURL    https://raw.githubusercontent.com/btbonval/LVDSA-Software/refs/heads/main/tampermonkey/Volunteer%20Signup%20Spreadsheet%20to%20LVDSA.user.js
// @downloadURL  https://raw.githubusercontent.com/btbonval/LVDSA-Software/refs/heads/main/tampermonkey/Volunteer%20Signup%20Spreadsheet%20to%20LVDSA.user.js
// @author       Bryan Bonvallet
// @match        https://docs.google.com/spreadsheets/d/1R1xD7_nopZWBWex4b0MWhAwT_RZ5tPFl7tIASj7gQaM/*
// @match        https://lvdsa.org/events/*
// @grant        GM_registerMenuCommand
// @grant        GM_openInTab
// ==/UserScript==

///// https://gist.githubusercontent.com/NoushadBug/dbc4e85487b2599f040831a6c36de397/raw/8ca433d54a386e70f324f2a4da9d6c38e0552c0a/googleSheetHelperFuncs.user.js
/*
This gist contains helper functions for interacting with Google Sheets using JavaScript. These functions can be used in Tampermonkey or any userscript to perform actions such as retrieving the value of a cell, getting the index of the currently selected cell, setting the index of the selected cell, and retrieving the value from a specified cell while preserving the previously selected cell.

Functions Included:
- getCurrentCellValue(): Get the value of the currently selected cell.
- getCurrentCellIndex(): Get the index of the currently selected cell.
- setCurrentCellIndex(cellIndex): Set the index of the selected cell.
- getValueFromCell(cellIndex): Get the value from a specified cell and restore the previously selected cell.
- setCellValue(cellIndex, value, preservePrevCellIndex = true): Set the value of a cell.
- simulateValueSet(value): Simulate setting the value of a cell (used internally).

These functions provide convenient ways to interact with Google Sheets programmatically and automate tasks within the spreadsheet interface.

Usage:
1. Copy and include the functions in your userscript or Tampermonkey script.
2. Call the functions as needed within your script to interact with Google Sheets.

Note: These functions are designed to work with the current version of Google Sheets as of the script's creation. If Google Sheets undergoes significant changes, some modifications may be required to ensure compatibility.

Feel free to modify and customize these functions to suit your specific needs. Happy scripting!
/*


/**
 * Get the value of the currently selected cell in Google Sheets.
 * @returns {string} The value of the current cell.
 */
function getCurrentCellValue() {
  var cellValue = document.querySelector('.cell-input').innerText;
  return cellValue.trim();
}

/**
 * Get the index of the currently selected cell in Google Sheets.
 * @returns {string} The index of the current cell (e.g., "A1", "B2").
 */
function getCurrentCellIndex() {
  var cellIndex = document.querySelector(".waffle-name-box").value;
  return cellIndex;
}

/**
 * Set the index of the selected cell in Google Sheets.
 * @param {string|object} cellIndex - The index of the cell to set (e.g., "A1", "B2") or a JSON object { column, row }.
 */
async function setCurrentCellIndex(cellIndex) {
  var inputBox = document.querySelector(".waffle-name-box");

  if (typeof cellIndex === "string") {
    inputBox.value = cellIndex;
  } else if (typeof cellIndex === "object") {
    var column = cellIndex.column || "";
    var row = cellIndex.row || "";
    inputBox.value = column + row;
  }

  // Trigger click event
  var clickEvent = new MouseEvent("click", {
    view: unsafeWindow,
    bubbles: true,
    cancelable: true,
  });
  inputBox.dispatchEvent(clickEvent);

  await delay(100); // Delay for smoother execution

  // Trigger enter key event
  var enterEvent = new KeyboardEvent("keydown", {
    key: "Enter",
    code: "Enter",
    keyCode: 13,
    view: unsafeWindow,
    bubbles: true,
    cancelable: true,
  });
  inputBox.dispatchEvent(enterEvent);
}

/**
 * Get the value from a specified cell in Google Sheets and restore the previously selected cell.
 * @param {string|object} cellIndex - The index of the cell to retrieve the value from (e.g., "A1", "B2") or a JSON object { column, row }.
 * @returns {string} The value of the specified cell.
 */
async function getValueFromCell(cellIndex, goPreviousCell = true) {
  if (goPreviousCell) {
    var previousCellIndex = getCurrentCellIndex();
  }

  if (typeof cellIndex === "string") {
    await setCurrentCellIndex(cellIndex);
  } else if (typeof cellIndex === "object") {
    await setCurrentCellIndex(cellIndex.column + cellIndex.row);
  }
  await delay(50);
  var cellValue = getCurrentCellValue();
  if (goPreviousCell) {
    await setCurrentCellIndex(previousCellIndex);
  }
  return cellValue;
}

/*
async function setCellValue(cellIndex, value, preservePrevCellIndex = true) {
  await setCurrentCellIndex(cellIndex);

  await simulateValueSet(value);
  await simulateValueSet(value);

  if (preservePrevCellIndex) {
    await setCurrentCellIndex(cellIndex);
  }
}

async function simulateValueSet(value) {
  var inputBox = document.querySelector('.cell-input');

  if (inputBox) {
    // Trigger click event
    nonReactive = true;
    var clickEvent = new MouseEvent('click', {
      view: window,
      bubbles: true,
      cancelable: true,
    });
    inputBox.dispatchEvent(clickEvent);
    nonReactive = false;

    await delay(80); // Delay for smoother execution

    // Trigger keydown event
    var keydownEvent = new KeyboardEvent('keydown', {
      key: 'Enter',
      code: 'Enter',
      keyCode: 13,
      view: window,
      bubbles: true,
      cancelable: true,
    });
    inputBox.dispatchEvent(keydownEvent);

    // Set the cell value
    inputBox.innerText = value;

    // Trigger input event
    var inputEvent = new Event('input', {
      bubbles: true,
      cancelable: true,
    });
    inputBox.dispatchEvent(inputEvent);

    // Trigger keydown event
    var keydownPress = new KeyboardEvent('keypress', {
      key: 'Enter',
      code: 'Enter',
      keyCode: 13,
      view: window,
      bubbles: true,
      cancelable: true,
    });
    inputBox.dispatchEvent(keydownPress);
  }
}
*/

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
/////

///// https://stackoverflow.com/a/34483399
function nextChar(c) {
    var u = c.toUpperCase();
    if (same(u,'Z')){
        var txt = '';
        var i = u.length;
        while (i--) {
            txt += 'A';
        }
        return (txt+'A');
    } else {
        var p = "";
        var q = "";
        if(u.length > 1){
            p = u.substring(0, u.length - 1);
            q = String.fromCharCode(p.slice(-1).charCodeAt(0));
        }
        var l = u.slice(-1).charCodeAt(0);
        var z = nextLetter(l);
        if(z==='A'){
            return p.slice(0,-1) + nextLetter(q.slice(-1).charCodeAt(0)) + z;
        } else {
            return p + z;
        }
    }
}

function nextLetter(l){
    if(l<90){
        return String.fromCharCode(l + 1);
    }
    else{
        return 'A';
    }
}

function same(str,char){
    var i = str.length;
    while (i--) {
        if (str[i]!==char){
            return false;
        }
    }
    return true;
}
/////

const HEADER_CHECK = {
    'A': 'First',
    'B': 'Last',
    'C': 'email',
    'D': 'phone',
    'E': 'zip',
}

// create arbitrary cutoff to prevent infinite loop. this can be changed.
const MAXROWS = 100;

// create arbitrary cutoff to prevent infinite loop. this can be changed.
const MAXCOL = 'AF';

async function read_people_data() {
    // Starting at A2 Header: First,	Last,	email,	phone,	zip
    let row = 2;
    for (let cell of Object.keys(HEADER_CHECK)) {
        let expected = HEADER_CHECK[cell];
        cell = cell + row.toString();
        let actual = await getValueFromCell(cell, false);
        if (actual !== expected) {
            throw `Bryan Script could not read correct header. For ${cell}, got ${actual} instead of ${expected}`;
        }
        /* handy debug tool.
        else {
            console.log('Checks out',cell,actual,expected);
        }
        */
    }

    let people_data = {};

    // read A3...A{N} until no more rows are left.
    let keep_processing = true;
    while (row < MAXROWS && keep_processing) {
        //break;
        row += 1;
        if (!people_data[row]) {
            people_data[row] = {'form links': []};
        }
        for (let cell of Object.keys(HEADER_CHECK)) {
            let column_name = HEADER_CHECK[cell];
            cell = cell + row.toString();
            let data = await getValueFromCell(cell, false);
            if (column_name === 'First' && !data) {
                // first name is blank, assume that's the end.
                keep_processing = false;
                delete people_data[row];
                break;
            }
            people_data[row][column_name] = data;
        }
    }
    console.log(people_data);
    return people_data;
}

async function read_column_data(URL, column, people_data) {
    let coldata = {
        'link': URL,
        'people': [],
    };
    let row=1;
    // read the column's name and URL first.
    let cell = `${column}2`;
    coldata['name'] = await getValueFromCell(cell, false);
    // we only need to read up to the last person.
    let person_as_row = Object.keys(people_data);
    let last_row = parseInt(person_as_row[person_as_row.length-1])+1;
    // read rows starting at 3 until no more rows are left.
    row = 3;
    while (row < last_row) {
        let cell = `${column}${row}`;
        let checked = await getValueFromCell(cell, false);
        if (!!checked) {
            // add the person to the column's form data
            coldata['people'].push(people_data[row]);
            // also add the form link to the person's data!
            people_data[row]['form links'].push(URL);
        }
        row += 1;
    }

    // don't show per-form for now
    //GM_registerMenuCommand(`Register people for ${coldata.name}`, _ => console.log(coldata));

    return coldata;
}

async function read_columns(people_data) {
    // start at column F
    let column = 'F';

    while (column !== MAXCOL) {
        // try to read the form's URL.
        let cell = `${column}1`;
        let col_link = await getValueFromCell(cell, false);
        if (!col_link) {
            // this column has no form URL, assume we hit the end of the columns.
            return false;
        }
        // we might also hit end of sheet size which seems to terminate the script :(

        await read_column_data(col_link, column, people_data);
        column = nextChar(column);
    }

    return people_data;
}

async function process_people_buttons(people_data) {
    for (let row of Object.keys(people_data)) {
        // deep copy the person data; this might not be necessary. overly cautious.
        let person = JSON.parse(JSON.stringify(people_data[row]));
        GM_registerMenuCommand(`Register all dates for ${person.First} ${person.Last}` , _ => {
            // deep copy form links
            let links = JSON.parse(JSON.stringify(person['form links']));
            // so we can get rid of them
            delete person['form links'];
            for (let link of links) {
                let url = new URL(link);
                url.search = new URLSearchParams(person);
                GM_openInTab(url.toString());
            }
        });
    }
}

// identify which data about a person goes into which field's id
const data_to_fieldname = {
    'First': 'form-first_name',
    'Last': 'form-last_name',
    'email': 'form-email',
    'phone': 'form-phone',
    'zip': 'form-zip_code',
};

function populate_data_into_form(query_params, attempts) {
    attempts += 1;
    // read the URL query parameters.
    let parameters = new URLSearchParams(window.location.search);
    for (let data_key of Object.keys(data_to_fieldname)) {
        let target = unsafeWindow.document.getElementById(data_to_fieldname[data_key]);
        if (!target && attempts < 3) {
            // try again in a moment.
            setTimeout(_ => populate_data_into_form(query_params, attempts), 250);
            return;
        }
        if (!target) {
            throw `Could not find ID ${data_to_fieldname[data_key]} for ${data_key}`;
        }
        console.log(parameters);
        target.value = parameters.get(data_key);
    }
}

(function() {
    'use strict';

    // For the Google Doc, support parsing the data.
    if (window.location.hostname === 'docs.google.com') {
        GM_registerMenuCommand('Process Sign Ups', _ => read_people_data()
                                                  .then(people_data => read_columns(people_data))
                                                  .then(people_data => process_people_buttons(people_data))
                              );
        //setTimeout(read_people_data().then(people_data => read_columns(people_data)), 500);
    }

    // For the form page, support populating the data (assuming it is present as query string parameters aka search)
    if (window.location.hostname === 'lvdsa.org' && !!window.location.search) {
        populate_data_into_form(window.location.search, 0);
    }
})();