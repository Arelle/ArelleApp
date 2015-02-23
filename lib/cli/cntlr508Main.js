/*
   Created on Apr 1, 2013

   This module is Arelle's controller in web interactive UI mode
   author: Mark V Systems Limited

   (c) Copyright 2013-2015 Mark V Systems Limited, All rights reserved.

*/

var webroot = '';
var cgi = '';
var i = location.href.indexOf("/arelleApp/");
if (i >= 0) {
	// when operating through pyBottle, path is root ("/") without /lib/ at end
	webroot = location.href.substr(0, i+10);
	cgi = location.href.substr(0, i) + "/cgi-bin/arelleApp/CntlrAppSvr";
}
var winStyle = 
	"body {overflow-y:scroll;}" + // need vert scrollbar if too tall 
	"h {font-family: Arial,Helvetica;font-size:18;color:#1a1a54;}\n" +
	"p, body, center, td, bl, li, input {font-family: Arial,Helvetica;font-size:12;color:#1a1a54;}\n" +
    "html, body {width: 100%;height: 100%;overflow: hidden;margin: 0px;background-color: #EBEBEB;}" +
"table {width:97%} table, th, td {border: 1px solid #87cefa;border-collapse:collapse;}  td th {padding: 3px 7px 2px 7px;} th {background-color:#87cefa; color:white} tr.alt {background-color:#e2f4ff;}";
var rlConn, rlOpenOrdinal = 0, rlCurrentTabOrdinal = '';

var multivariateView = {
	filingIds: [],
	variables: ["SALE","COGS","GP","XSGA","XRD","EPSPI","EPSFI"],
	heatMap: false
};

function cntlr508Win(){
	// if no database connection, do that first
	if (!verifyDBconn()) {
		showConnectToDBform();
		return;
	}

	// clean out any prior-selected filingIds
	multivariateView.filingIds = []; // empty list
	
	loadWindow({
		name: "startupScreen",
		heading: "Welcome to Experimental Voice Over App",
		style: winStyle,
		align: "center",
		form: [
			{type: "para", value: "Please select:"},
			{type: "radio", name: "open", value: "open-multivariate", checked: null, label: "Multivariate"},
			{type: "radio", name: "open", value: "single-filing", label: "Single Filing"},
			{type: "button", name: "next", value: "Next", onclick: "mainFormNextAction()"},
			{type: "button", name: "dbConnection", value: "Database Connection", onclick: "showConnectToDBform()"}
		]
	});
}

function mainFormNextAction() {
	openFiling(formInputValue("open"));
}

function verifyDBconn() {
    if (!rlConn) {
        rlConn = readCookie("rlConnection");
        if (rlConn && rlConn.length > 0) {
            rlConn = Base64.decode(rlConn).split('|');
        } else {
            rlConn = new Array("", "", "", "", "");
        }
    }
    return (rlConn[0].length > 0);
}

function showConnectToDBform() {
	verifyDBconn();
	loadWindow({
		name: "connectToDB",
		heading: "Connect to database",
		style: winStyle,
		align: "center",
		form: [
			{type: "para", value: "Enter Database connection parameters:"},
            {type:"text", name: 'address', label:'Address', size:'20', value:rlConn[0]},
    		{type:"text", name: 'port', label:'Port', size:'20', value:rlConn[1]},
    		{type:"text", name: 'user', label:'User', size:'20', value:rlConn[2]},
    		{type:"password", name:"password", label:"Password", size:'20', value:rlConn[3]},
    		{type:"text", name: 'database', label:'Database', size:'20', value:rlConn[4]},
    		{type:"text", name: 'timeout', label:'Timeout', size:'20', value:rlConn[5]},
    		{type:"button", name:"connect", value:"Connect", onclick: "testDBconnection()"}
	    ]
	});
}

function testDBconnection() {
    rlConn[0] = formInputValue('address');
    rlConn[1] = formInputValue('port');
    rlConn[2] = formInputValue('user'); 
    rlConn[3] = formInputValue('password'); 
    rlConn[4] = formInputValue('database');
    rlConn[5] = formInputValue('timeout');
    createCookie("rlConnection", Base64.encode(rlConn.join("|")), 365 * 5);
    urlApiResultsFunction("Test Database Connection", cgi + "/testDBconnection", function(results){
        cntlr508Win();
    });
}

function openFiling(openMode, filingsTable) {
    var filingId = null;
    // get previous filing selection parameters
    args = readCookie("rlFilingSelection");
    if (args && args.length >= 3) {
        args = Base64.decode(args).split('\t');
    } else {
        args = new Array("", "", "", "", "", "");
    }
    var table = null;
    if (filingsTable) {
    	table = {
    	    header: "Filing,Name,Tckr Sym,Form Type,Timestamp,URL,SIC,Creation Software,Messages",
    	    selectionCheckbox: true,
    		widths: "132,148,42,42,124,48,36,64,400",
    		align: "left,left,left,left,left,left,left,left,left",
			rows: filingsTable.rows
		};
    }
	loadWindow({
		name: "openSingleFiling",
		heading: (openMode == "single-filing") ? "Open Single Filing" : 
			      ((openMode == "add-to-multivariate") ? "Add to Multivariate Grid" : "Open Multivariate Grid"),
			
		style: winStyle,
		align: "center",
		form: [
			{type: "table", value: table},
			{type: "para", value: "Filters:"},
			{type: "para", fontsize: "1", value: "Match with * and ? wildcards.  Search is case insensitive.  (End with * to match rest of value.)  If first character is ~ then the rest is a posix regex pattern (case insensitive)."},
			{type: "text", name: "number", label: "Number", value: args[0], size: "20"},
			{type: "text", name: "name", label: "Name", value: args[1], size: "20"},
			{type: "text", name: "tickerSymbol", label: "Ticker Symbol", value: args[5], size: "20"},
			{type: "text", name: "formType", label: "Form Type", value: args[4], size: "20"},
			{type: "text", name: "date", label: "Date", value: args[2], size: "20"},
			{type: "text", name: "sic", label: "SIC", value: args[3], size: "20"},	
			{type: "button", name: "filter", value: "Filter", 
					onclick: "openFilingAction(\"refilter\",\"{0}\")".format(openMode)},
			{type: "button", name: "open", 
			        value: ((openMode == "add-to-multivariate") ? "Add Filings" : "Open"), 
					onclick: "openFilingAction(\"open\",\"{0}\")".format(openMode)}
		]
	});
}

function openFilingAction(action, openMode) {
	if (action == "refilter") {
		args = new Array(formInputValue("number"),  formInputValue("name"), formInputValue("date"), formInputValue("sic"), formInputValue("formType"), formInputValue("tickerSymbol"));
	    createCookie("rlFilingSelection", Base64.encode(args.join('\t')), 365 * 5);
	    urlApiResultsFunction("Load Filings", 
	    					  cgi + "/grid/filings?filing=" + args[0] + "&name=" + args[1] + "&date=" + args[2] + "&sic=" + args[3] + "&formtype=" + args[4] + "&ticker=" + args[5], 
	    					  function(results){
	        						openFiling(openMode, results);
	    					  });
    } else if (action == "open") {
    	if (openMode == "single-filing") {
    	} else if (openMode == "open-multivariate" || openMode == "add-to-multivariate" ) {
    		openMultivariate(checkedIds());
    	}
    }
}

function openMultivariate(filingIds) {
	// add filingIds to multivariateView.filingIds
	for (var i=0; i<filingIds.length; i+=1) 
		if (multivariateView.filingIds.indexOf(filingIds[i]) == -1)
			multivariateView.filingIds.push(filingIds[i]);
	showMultivariateGrid();
}



function showMultivariateGrid() {
    urlApiResultsFunction("Show Multivariate Grid", 
		cgi + "/grid/multivariateGrid" +
			"?filingIds=" + multivariateView.filingIds.join(',') + 
			"&variables=" + multivariateView.variables.join(','),
		function(results){
			table = {
			    header: "Filing",
	    	    selectionCheckbox: true,
				widths: "200",
				align: "left",
				rows: results.rows
			};
			// add variables columns
			for (var iCol=0; iCol<multivariateView.variables.length; iCol+=1) {
				table.header += "," + multivariateView.variables[iCol];
				table.widths += ",100";
				table.align += ",right";
			}
			loadWindow({
				name: "multivariate",
				heading: "Multivariate",
				style: winStyle,
				align: "center",
				form: [
					{type: "table", value: table},
					{type: "button", name: "addFiling", value: "Add Filings", 
					 onclick: "openFiling(\"add-to-multivariate\");"},
					{type: "button", name: "removeFiling", value: "Remove Filings", 
					 onclick: "deleteCheckedFilings();"},
					{type: "button", name: "startOver", value: "Start Over", 
					 onclick: "cntlr508Win();"}
				]
			});
		});
}

function deleteCheckedFilings() {
	var checkedIdsToDelete = checkedIds();
	for (var i=0; i<checkedIdsToDelete.length; i+=1) {
		var j = multivariateView.filingIds.indexOf(checkedIdsToDelete[i]);
		if (j > -1)
			multivariateView.filingIds.splice(j, 1);
	}
	showMultivariateGrid();
}


function loadWindow(spec) {
	var t = "<html><head>\n";
	if ("style" in spec) {
		t += "<style>\n{0}\n</style>\n".format(spec.style);
	}
	t += "</head><body>\n";
	if (spec.align == "center") {
		t += "<center>\n";
	}
	if ("heading" in spec) {
		t += "<h>{0}</h><br/>\n".format(spec.heading);
	}
	if ("form" in spec) {
		t += "<form>\n";
		for (var i=0; i<spec.form.length; i++) {
			var item = spec.form[i];
			switch (item.type) {
    		case "para": 
    			if ("fontsize" in item)
			    	t += "<font size={0}>".format(item.fontsize);
		    	t += "<p>{0}</p>".format(item.value);
    			if ("fontsize" in item)
			    	t += "</font>".format(item.fontsize);
			    t += "\n";
		    	break;
		    case "radio":
				t += "<input type='radio' name='{0}' value='{1}' {2}>{3}</input><br/>\n".format(
					item.name, item.value, ("checked" in item)?"checked":"", item.label);
				break;
		    case "button":
				t += "<input type='button' name='{0}' value='{1}' {2}/><br/>\n".format(
					item.name, item.value, 
					("onclick" in item) ? "onclick='{0}'".format(item.onclick) : "");
				break;
			case "text":
			case "password":
				t += "{0}<input type='{1}' name='{2}' value='{3}' {4}/><br/>\n".format(
					item.label, item.type, item.name, item.value, 
					(("size" in item) ? "size='{0}'".format(item.size) : "") +
					(("onclick" in item) ? "onclick='{0}'".format(item.onclick) : ""));
				break;
			case "table":
				var table = item.value;
				if (table == null)
					break;
				t += "<table>\n";
				if ("header" in table) {
					t += "<tr>";
					if (table.selectionCheckbox)
						t += "<th><input type='checkbox' onchange='onHeaderCheckboxChanged(this)'/></th>";
					headers = table.header.split(",");
					for (var j=0; j<headers.length; j++) 
						t += "<th>{0}</th>".format(headers[j]);
					t += "</tr>\n";
				}
				if ("rows" in table) {
					for (var j=0; j<table.rows.length; j++) {
						t += "<tr{0}>".format((j & 1)?" class='alt'":"");
						var rowId = table.rows[j].id;
						var rowData = table.rows[j].data;
						if (table.selectionCheckbox)
							t += "<td><input type='checkbox' name='{0}'/></th>".format(rowId)
						;
						for (var k=0; k<rowData.length; k++) {
							var colData = rowData[k];
							t += "<td>{0}</td>".format((colData.length > 0)?colData:"&#160;");
						}
						t += "</tr>\n";
					}
				}
				t += "</table>\n";
				break;
  			}
		}
		t += "</form>\n";
	}
	if (spec.align == "center") {
		t += "</center>\n";
	}
	t += "</body></html>\n";
	// uncomment for debugging
	// alert("window {0}\n{1}".format(spec.name, t));
	document.write(t);
	document.close();
}

function formInputValue(name) {
	var inputNodes = document.getElementsByName(name);
	for (var i = 0; i < inputNodes.length; i++) {
		var inputNode = inputNodes[i];
		if (inputNode.type == "radio") {
		    if (inputNode.checked) {
		        return inputNode.value;
		    }
		} else {
			return inputNode.value;
		}
	}
	alert("no field " + name);
	return null;
}

function onHeaderCheckboxChanged(cb) {
	var inputNodes = document.getElementsByTagName("input");
	for (var i = 0; i < inputNodes.length; i++) {
		var inputNode = inputNodes[i];
		if (inputNode.type == "checkbox")
			inputNode.checked = cb.checked;
	}
}

function checkedIds() {
	var inputNodes = document.getElementsByTagName("input");
	var checkedIds = []
	for (var i = 0; i < inputNodes.length; i++) {
		var inputNode = inputNodes[i];
		if (inputNode.type == "checkbox")
			if (inputNode.checked && inputNode.name)
				checkedIds.push(inputNode.name	);
	}
	return checkedIds;
}

String.prototype.format = function (){
    var args = arguments;
    return this.replace(/\{\{|\}\}|\{(\d+)\}/g, function (curlyBrack, index) {
        return ((curlyBrack == "{{") ? "{" : ((curlyBrack == "}}") ? "}" : args[index]));
    });
};

function urlApiResultsFunction(activity, url, resultsFunction) {
	//alert("before svr call " + activity);
	/* v3.0
	dhtmlxAjax.get(url, function(loader){
	*/
	dhx4.ajax.get(url, function(loader){
		//alert("svr call " + activity + "\n results=" + loader.xmlDoc.responseText);
        results = JSON.parse(loader.xmlDoc.responseText);
        resultsFunction(results);
    });
}

function execute(activity, mode, script, responseFunction, responseArg, traceResponse, traceRequest) {
    rlStatusbar.setText(activity);
	if (traceRequest)
		alert(activity + " " + mode + " request:\n" + script);
    var req = new XMLHttpRequest();
	var reqUrl = rlConnUrl + ((mode == "GET" && script) 
				? ("/tp/gremlin?script=" + encodeURIComponent(script) + "&nocache=")
				:  ((mode == "POST")? "/tp/gremlin?nocache=" : "?nocache=")
	            ) + new Date().getTime();
	req.open(mode, reqUrl, true); //, rlConn[2], rlConn[3]);
    if (rlConnAuthHdr) {
        //req.setRequestHeader('Authorization', rlConnAuthHdr);
        req.withCredentials = true;
    }
    req.timeout = 20000;
    req.onreadystatechange = function () {
        rlStatusbar.setText("last readyState=" + req.readyState + " last status=" + req.status);
        if (req.readyState == 4) {
            if (req.status == 200) {
                rlStatusbar.setText(activity + ", response received");
	            // TBD - make this menu settable to show alert
	            if (traceResponse)
				  alert("responseType=" + req.responseType + "\nresponse=\n" + req.responseText);
			    var jsonResponse = eval("(" + req.responseText + ")");
			    // JSON.parse(req.responseText) hangs here
                responseFunction(jsonResponse, responseArg);
            }else{
                alert("http failed status = " + req.statusText + " (" + req.status + ")" +
                      "\nresponse=" + req.responseText);
                rlStatusbar.setText(activity + ", failed status=" + req.statusText);
            }
        }
    };
    req.ontimeout = function () { 
        alert("Timed out!!!"); 
    };
    //req.setRequestHeader("Connection", "close");
    if (mode == "GET") {
	    req.send();
    } else {
        //alert("URL: \n" + rlConnUrl + "/tp/gremlin" + "\n\nGremlin:\n\n" + connArg);
        req.setRequestHeader("User-agent", "Arelle/1.0");
        req.setRequestHeader("Accept", "application/json");
        req.setRequestHeader("Content-Type", "application/json");
        var POSTarg = Base64._utf8_encode(JSON.stringify({"script":script}));
        req.send(POSTarg);
    }
}

function createCookie(name,value,days) {
    var expires;
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		expires = "; expires=" + date.toGMTString();
	}
	else expires = "";
	document.cookie = name+"=" + escape(value) + expires + "; path=/";
}

function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return unescape(c.substring(nameEQ.length,c.length));
	}
	return null;
}

function eraseCookie(name) {
	createCookie(name,"",-1);
}

var Base64 = { 
	// private property
	_keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
 
	// public method for encoding
	encode : function (input) {
		var output = "";
		var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
		var i = 0;
 
		input = Base64._utf8_encode(input);
 
		while (i < input.length) {
 
			chr1 = input.charCodeAt(i++);
			chr2 = input.charCodeAt(i++);
			chr3 = input.charCodeAt(i++);
 
			enc1 = chr1 >> 2;
			enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
			enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
			enc4 = chr3 & 63;
 
			if (isNaN(chr2)) {
				enc3 = enc4 = 64;
			} else if (isNaN(chr3)) {
				enc4 = 64;
			}
 
			output = output +
			this._keyStr.charAt(enc1) + this._keyStr.charAt(enc2) +
			this._keyStr.charAt(enc3) + this._keyStr.charAt(enc4);
 
		}
 
		return output;
	},
 
	// public method for decoding
	decode : function (input) {
		var output = "";
		var chr1, chr2, chr3;
		var enc1, enc2, enc3, enc4;
		var i = 0;
 
		input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
 
		while (i < input.length) {
 
			enc1 = this._keyStr.indexOf(input.charAt(i++));
			enc2 = this._keyStr.indexOf(input.charAt(i++));
			enc3 = this._keyStr.indexOf(input.charAt(i++));
			enc4 = this._keyStr.indexOf(input.charAt(i++));
 
			chr1 = (enc1 << 2) | (enc2 >> 4);
			chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
			chr3 = ((enc3 & 3) << 6) | enc4;
 
			output = output + String.fromCharCode(chr1);
 
			if (enc3 != 64) {
				output = output + String.fromCharCode(chr2);
			}
			if (enc4 != 64) {
				output = output + String.fromCharCode(chr3);
			}
 
		}
 
		output = Base64._utf8_decode(output);
 
		return output;
 
	},
 
	// private method for UTF-8 encoding
	_utf8_encode : function (string) {
		string = string.replace(/\r\n/g,"\n");
		var utftext = "";
 
		for (var n = 0; n < string.length; n++) {
 
			var c = string.charCodeAt(n);
 
			if (c < 128) {
				utftext += String.fromCharCode(c);
			}
			else if((c > 127) && (c < 2048)) {
				utftext += String.fromCharCode((c >> 6) | 192);
				utftext += String.fromCharCode((c & 63) | 128);
			}
			else {
				utftext += String.fromCharCode((c >> 12) | 224);
				utftext += String.fromCharCode(((c >> 6) & 63) | 128);
				utftext += String.fromCharCode((c & 63) | 128);
			}
 
		}
 
		return utftext;
	},
 
	// private method for UTF-8 decoding
	_utf8_decode : function (utftext) {
		var string = "";
		var i = 0;
		var c = c1 = c2 = 0;
 
		while ( i < utftext.length ) {
 
			c = utftext.charCodeAt(i);
 
			if (c < 128) {
				string += String.fromCharCode(c);
				i++;
			}
			else if((c > 191) && (c < 224)) {
				c2 = utftext.charCodeAt(i+1);
				string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
				i += 2;
			}
			else {
				c2 = utftext.charCodeAt(i+1);
				c3 = utftext.charCodeAt(i+2);
				string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
				i += 3;
			}
		}
		return string;
	}
}
