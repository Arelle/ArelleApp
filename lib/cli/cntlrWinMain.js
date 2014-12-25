/*
   Created on Apr 1, 2013

   This module is Arelle's controller in web interactive UI mode
   author: Mark V Systems Limited

   (c) Copyright 2013-2015 Mark V Systems Limited, All rights reserved.

*/

var rlLayout, rlMenu, rlToolbar, rlStatusbar, rlTabbarTopLeft, rlTabbarTopRight, rlTabbarBottom;
var rlPopupWindows, rlOpenOrdinal = 0, rlCurrentTabOrdinal = '';
var rlFilingEvent;
var rlFilingViews = {};
var rlConnAuthHdr, rlConnUrl, rlConn;
var rlSkin = 'dhx_skyblue';
var webroot = '';

function cntlrMainWin(){
    rlLayout = new dhtmlXLayoutObject(document.body, "3U", rlSkin);
    rlLayout.cells("a").setWidth(250);
    rlLayout.cells("c").setHeight(250);
    rlLayout.cells("a").hideHeader();
    rlLayout.cells("b").hideHeader();
    rlLayout.cells("c").hideHeader();
    rlMenu = rlLayout.attachMenu();
    rlMenu.setImagePath(webroot + "/lib/UI/imgs/");
    rlMenu.setIconsPath(webroot + "/lib/cli/images/");
    rlMenu.loadXML(webroot + "/lib/cli/menuWinMain.xml");
    rlMenu.attachEvent("onClick", function(id){
        if (id == "connect")
           connectToDB();
        else if (id == "open")
            openFiling();
        else if (id == "close")
            closeFiling();
        else
           alert("Menu entry "+id+" was clicked");
    });
    rlToolbar = rlLayout.attachToolbar();
    rlToolbar.setIconsPath(webroot + "/lib/cli/images/");
    rlToolbar.loadXML(webroot + "/lib/cli/toolbarWinMain.xml");
    rlToolbar.attachEvent("onClick", function(id){
        if (id == "openDatabaseChooser")
            openFiling();
        else if (id == "close")
            closeFiling();
        else
            alert("Toolbar button with name "+id+" was clicked");
    });
    rlStatusbar = rlLayout.attachStatusBar(); 
    rlTabbarTopLeft =  rlLayout.cells("a").attachTabbar();    
    rlTabbarTopRight =  rlLayout.cells("b").attachTabbar();    
    rlTabbarBottom =  rlLayout.cells("c").attachTabbar();
    rlTabbarTopLeft.setImagePath(webroot + "/lib/UI/imgs/");
    rlTabbarTopRight.setImagePath(webroot + "/lib/UI/imgs/");
    rlTabbarBottom.setImagePath(webroot + "/lib/UI/imgs/");
    rlTabbarTopLeft.attachEvent("onSelect", onTabSelect);
    rlTabbarTopRight.attachEvent("onSelect", onTabSelect);
    rlTabbarBottom.attachEvent("onSelect", onTabSelect);
    rlPopupWindows = new dhtmlXWindows();
    rlPopupWindows.setImagePath(webroot + "/lib/UI/imgs/");
}

function onTabSelect(id, lastId) {
	var idParts = id.split('-');
	if (idParts.length > 1) {
		rlCurrentTabOrdinal = idParts[idParts.length - 1];
	} else {
		rlCurrentTabOrdinal = '1';
	}
	return true;
}

function connectToDB() {
    var win = rlPopupWindows.createWindow({
        id:"connectToDB",
        x:20, y:30, width:260, height:220, center:true
	 //        onClose:function(){return true;}
    });
    win.setText("Connect to database");
    if (!rlConn) {
        rlConn = readCookie("rlConnection");
        if (rlConn && rlConn.length > 0) {
            rlConn = Base64.decode(rlConn).split('|');
        } else {
            rlConn = new Array("", "", "", "", "");
        }
    }
    var form = win.attachForm([
            {type: "settings", position: "label-left", labelWidth: 60, inputWidth: 170, labelAlign: "left"},
            {type:"input", name: 'address', label:'Address', value:rlConn[0]},
    		{type:"input", name: 'port', label:'Port', value:rlConn[1]},
    		{type:"input", name: 'user', label:'User', value:rlConn[2]},
    		{type:"password", name:"password", label:"Password", value:rlConn[3]},
    		{type:"input", name: 'database', label:'Database', value:rlConn[4]},
    		{type:"input", name: 'timeout', label:'Timeout', value:rlConn[5]},
    		{type:"button", name:"connect", value:"Connect", offsetLeft: 80}]);
    form.attachEvent("onButtonClick",function(id){
        rlConn[0] = form.getItemValue('address');
        rlConn[1] = form.getItemValue('port');
        rlConn[2] = form.getItemValue('user'); 
        rlConn[3] = form.getItemValue('password'); 
        rlConn[4] = form.getItemValue('database');
        rlConn[5] = form.getItemValue('timeout');
        createCookie("rlConnection", Base64.encode(rlConn.join("|")), 365 * 5);
        urlApiResultsFunction("Test Database Connection", "/testDBconnection", function(results){
	        rlStatusbar.setText("Connected to " + results["name"]);
        });
        win.close();
    })
}

function openFiling() {
    var filingId = null, win, layout, grid, form;
    win = rlPopupWindows.createWindow({
        id:"openFiling",
        x:20, y:30, width:800, height:400, center:true
        /*
	    onClose:function(){
	    	//layout.unload();
	    	//grid.unload();
	        return true;
	    }
	    */
    });
    win.setText("Select a filing to open");
    grid = win.attachGrid();
    grid.setHeader("Filing,Name,Timestamp,URL,Creation Software,Messages");
    grid.setInitWidths("132,200,120,50,100,400");
    grid.setColAlign("left,left,left,left,left,left");
    grid.setColTypes("ro,ro,ro,ro,ro,ro");
    grid.setColSorting("str,str.str,str,str,str");
    grid.init();
    grid.setSkin(rlSkin);
    grid.attachEvent("onRowSelect", function(id,ind){
        win.close();
    	setTimeout(function(){
				      viewFiling(id);
					}, 200);
        return true;
    });
    grid.load("/grid/filings", "json");
    rlStatusbar.setText("Select a filing to view...");
}

function closeFiling() {
	if (rlCurrentTabOrdinal in rlFilingViews) {
		var filingView = rlFilingViews[rlCurrentTabOrdinal];
		var tabItems = filingView['tabItems'];
		for (var i=0; i<tabItems.length; i++) {
			var tabItem = tabItems[i];
			tabItem['tabBar'].removeTab(tabItem['tabName'],true);
			// tabItem['grid'].destructor();
		}
		delete rlFilingViews[rlCurrentTabOrdinal];
	}
}

function onSelectObject(filingView, id, clickedTabName) {
	try {
		var tabItems = filingView['tabItems'];
		for (var i=0; i<tabItems.length; i++) {
			var tabItem = tabItems[i];
			if (clickedTabName != tabItem['tabName'] && tabItem['showObjectFunction']) {
				tabItem['showObjectFunction'](tabItem['grid'], filingView['filingId'], id, tabItem['arcrole']);
			}
		}
	} catch (err) {
		alert("Exception in onSelectObject for " + clickedTabName + "\n\nError: " + err.message);
	}
	return true;
}

function propertyGridShowObject(grid, filingId, id) {
    grid.clearAll();
    grid.load("/grid/properties?filingId=" + filingId + "&id=" + id, 'json');
}

function treeGridShowObject(grid, filingId, id, arcrole) {
    urlApiResultsFunction("Selecting relationships", 
                    	  "/select/relationships?id=" + id + "&arcrole=" + arcrole, 
                          function(results){
    	var id = results[0];
    	grid.selectRowById(id);
	    grid.openItem(grid.getParentId(id));
		grid.showRow(id);
    });
}

function aspectsGridShowObject(grid, filingId, id) {
    urlApiResultsFunction("Selecting aspects", "/select/aspects?id=" + id, function(results){
		grid.selectRowById(results[0], false, true, false);
    });
}

function dataPointsGridShowObject(grid, filingId, id) {
    urlApiResultsFunction("Selecting data point", "/select/datapoints?id=" + id, function(results){
        grid.selectRowById(results[0], false, true, false);
    });
}

function newGridItem(name, filingView, tabBar, width, colHeaders, colWidths, colAligns, multiline, colTypes, colSorts, arcrole, loadUrl, setInitialViewActive, onRowSelectFunction, showObjectFunction) {
	var tabNameSuffix = '';
	var tabLabelSuffix = '';
	var tabWidth = width;
	if (rlOpenOrdinal > 1) {
		tabNameSuffix = '-' + rlOpenOrdinal;
		tabLabelSuffix = ' - ' + rlOpenOrdinal;
		tabWidth += 16
	}
	var tabName = name + "Tab" + tabNameSuffix;
    tabBar.addTab(tabName, name + tabLabelSuffix, tabWidth.toString() + "px");
    var grid = tabBar.cells(tabName).attachGrid();
    grid.setHeader(colHeaders);
    grid.setInitWidths(colWidths);
    grid.setColAlign(colAligns);
    if (multiline)
	    grid.enableMultiline(true);
    grid.setColTypes(colTypes);
    grid.setColSorting(colSorts);
    grid.setImagePath(webroot + "/lib/UI/imgs/");
    grid.setIconsPath(webroot + "/lib/cli/images/");
    grid.setImageSize(1,1);
    grid.setSerializationLevel(true);
    grid.enableSmartRendering(true);
    grid.enablePreRendering(50);
    //grid.startFastOperations();
    grid.init();
    grid.setSkin(rlSkin);
    if (onRowSelectFunction) {
	    grid.attachEvent("onRowSelect", function(id,ind){ // onRowSelect, onRowDblClicked
	    	setTimeout(function(){
  						onRowSelectFunction(filingView, id, tabName);
  						}, 300);
    	});
    }
    var gridObj = {};
    gridObj['grid'] = grid;
    gridObj['name'] = name;
    gridObj['tabBar'] = tabBar;
    gridObj['tabName'] = tabName;
    gridObj['filingId'] = filingView['filingId'];
    if (loadUrl) {
    	loadUrl += "?filingId=" + filingView['filingId'];
    	if (arcrole)
    		loadUrl += "&arcrole=" + arcrole;
    }
    gridObj['loadUrl'] = loadUrl;
    gridObj['arcrole'] = arcrole;
    gridObj['setInitialViewActive'] = setInitialViewActive;
    gridObj['showObjectFunction'] = showObjectFunction;
    filingView['tabItems'].push(gridObj);
}

function viewFiling(filingId) {
	var filingView = {};
	filingView['filingId'] = filingId;
	var tabItems = new Array();
	filingView['tabItems'] = tabItems;
	rlOpenOrdinal += 1;
	rlCurrentTabOrdinal = rlOpenOrdinal.toString();
	rlFilingViews[rlCurrentTabOrdinal] = filingView;
	newGridItem("Messages", filingView, rlTabbarBottom, 60,
				"Seq,Code,Level,Text",
				"32,180,120,600",
				"right,left,left,left", true,
				"ro,ro,ro,ro",
				"str,str,str,str",
				null, "/grid/messages", true, onSelectObject, null);
	newGridItem("Fact List", filingView, rlTabbarTopRight, 60,
				"Name,Line,ContextRef,Unit,Value",
				"200,60,100,80,200",
				"left,left,left,left,left", false,
				"ro,ro,ro,ro,ro",
				"str,str,str,str,str",
				null, "/grid/datapoints", true, onSelectObject, dataPointsGridShowObject);
	newGridItem("DTS", filingView, rlTabbarTopLeft, 32,
				"Document",
				"400",
				"left", false,
				"tree",
				"str",
				null, "/grid/DTS", true, null, null);
	newGridItem("Properties", filingView, rlTabbarTopLeft, 72,
				"Property,Value",
				"100,200",
				"left,left", false,
				"tree,ro",
				"str,str",
				null, null, false, null, propertyGridShowObject);
	newGridItem("Aspects", filingView, rlTabbarBottom, 60,
				"Label,Name,Period,Balance,Data Type,Base Type",
				"300,200,60,60,140,140",
				"left,left,left,left,left,left", false,
				"ro,ro,ro,ro,ro,ro",
				"str,str,str,str,str,str",
				null, "/grid/aspects", false, onSelectObject, aspectsGridShowObject);
	newGridItem("Presentation", filingView, rlTabbarTopRight, 72,
				"Name,Type,References",
				"400,100,200",
				"left,left,left", false,
				"tree,ro,ro",
				"str,str,str",
				"http://www.xbrl.org/2003/arcrole/parent-child", 
				"/grid/relationships", false, onSelectObject, treeGridShowObject);
	newGridItem("Calculation", filingView, rlTabbarTopRight, 68,
				"Name,Weight,Balance",
				"400,50,70",
				"left,right,left", false,
				"tree,ro,ro",
				"str,str,str",
				"http://www.xbrl.org/2003/arcrole/summation-item", 
				"/grid/relationships", false, onSelectObject, treeGridShowObject);
	newGridItem("Dimensions", filingView, rlTabbarTopRight, 72,
				"Name,Arcrole,Closed,Usable",
				"400,120,50,50",
				"left,left,left,left", false,
				"tree,ro,ro,ro",
				"str,str,str,str",
				"XBRL-dimensions", "/grid/relationships", false, onSelectObject, treeGridShowObject);
	// load grids
	for (var i=0; i<tabItems.length; i++) {
		var tabItem = tabItems[i];
		if (tabItem['loadUrl']) {
			tabItem['grid'].load(tabItem['loadUrl'], "json");
            if (tabItem['setInitialViewActive'])
				tabItem['tabBar'].setTabActive(tabItem['tabName'])
		}
	}

}

function urlApiResultsFunction(activity, url, resultsFunction) {
	//alert("before svr call " + activity);
	dhtmlxAjax.get(url, function(loader){
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
