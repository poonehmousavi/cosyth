// Google Apps Script: paste into Extensions > Apps Script of a Google Sheet, then Deploy > New deployment > Web app
// (Execute as: Me; Who has access: Anyone). Copy the web app URL into index.html (RESULTS_URL).
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var raw = e.postData.contents, d = {};
  try { d = JSON.parse(raw); } catch (err) {}
  if (sheet.getLastRow() === 0) sheet.appendRow(['received_utc', 'status', 'study', 'participant', 'n_done', 'json']);
  var n = d.n_done || (d.results ? d.results.length : '');
  sheet.appendRow([new Date().toISOString(), d.status || '', d.study || '', d.participant || '', n, raw]);
  return ContentService.createTextOutput('ok');
}
function doGet() { return ContentService.createTextOutput('listening-test results endpoint is up'); }
