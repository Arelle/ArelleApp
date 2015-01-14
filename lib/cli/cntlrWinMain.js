/*
   Created on Apr 1, 2013

   This module is Arelle's controller in web interactive UI mode
   author: Mark V Systems Limited

   (c) Copyright 2013-2015 Mark V Systems Limited, All rights reserved.

*/

var rlLayout, rlMenu, rlToolbar, rlStatusbar, rlTabbarTopLeft, rlTabbarTopRight, rlTabbarBottom;
var rlPopupWindows, rlOpenOrdinal = 0, rlCurrentTabOrdinal = '';
var rlFilingEvent;
var rlObjectViews = {};
var rlConnAuthHdr, rlConnUrl, rlConn;
var rlSkin = 'dhx_skyblue';
var webroot = '';
var cgi = '';
if (location.href.substr(location.href.length-11, 11) == "/arelleApp/") {
	// when operating through pyBottle, path is root ("/") without /lib/ at end
	webroot = location.href.substr(0, location.href.length-1);
	cgi = location.href.substr(0, location.href.length-11) + "/cgi-bin/arelleApp/CntlrAppSvr";
}

function cntlrMainWin(){
    rlLayout = new dhtmlXLayoutObject(document.body, "3U", rlSkin);
    rlLayout.cells("a").setWidth(250);
    rlLayout.cells("c").setHeight(250);
    rlLayout.cells("a").hideHeader();
    rlLayout.cells("b").hideHeader();
    rlLayout.cells("c").hideHeader();
    rlMenu = rlLayout.attachMenu();
    /* dhtmlx v 3.0
    rlMenu.setImagePath(webroot + "/lib/UI/imgs/");
    rlMenu.setIconsPath(webroot + "/cli/images/");
    rlMenu.loadXML(webroot + "/cli/menuWinMain.xml");
    */
    //rlMenu.setImagePath(webroot + "/UI/imgs/");
    rlMenu.setIconsPath(webroot + "/UI/imgs/");
    //rlMenu.setIconsPath(webroot + "/cli/images/");
    rlMenu.loadStruct(webroot + "/cli/menuWinMain.xml");
    rlMenu.attachEvent("onClick", function(id){
        if (id == "connect")
           connectToDB();
        else if (id == "open_filing")
            openFiling("openFiling");
        else if (id == "open_document")
            openDocument();
        else if (id == "open_multivariate")
        	openFiling("openMultivariateGrid");
        else if (id == "close")
            closeObjectView();
        else if (id == "test_multivariate_COST2014sample")
        	doTest(id);
        else
           alert("Menu entry "+id+" was clicked");
    });
    rlToolbar = rlLayout.attachToolbar();
    /* dhtmlx v 3.0
    rlToolbar.setIconsPath(webroot + "/cli/images/");
    rlToolbar.loadXML(webroot + "/cli/toolbarWinMain.xml");
    */
    rlToolbar.setIconsPath(webroot + "/cli/images/");
    rlToolbar.loadStruct(webroot + "/cli/toolbarWinMain.xml");
    rlToolbar.attachEvent("onClick", function(id){
        if (id == "openDatabaseChooser")
            openFiling("openFiling");
        else if (id == "close")
            closeObjectView();
        else
            alert("Toolbar button with name "+id+" was clicked");
    });
    rlStatusbar = rlLayout.attachStatusBar(); 
    rlTabbarTopLeft =  rlLayout.cells("a").attachTabbar();    
    rlTabbarTopRight =  rlLayout.cells("b").attachTabbar();    
    rlTabbarBottom =  rlLayout.cells("c").attachTabbar();
    /* dhtmlx v 3.0
    rlTabbarTopLeft.setImagePath(webroot + "/UI/imgs/");
    rlTabbarTopRight.setImagePath(webroot + "/UI/imgs/");
    rlTabbarBottom.setImagePath(webroot + "/UI/imgs/");
    */
    rlTabbarTopLeft.attachEvent("onSelect", onTabSelect);
    rlTabbarTopRight.attachEvent("onSelect", onTabSelect);
    rlTabbarBottom.attachEvent("onSelect", onTabSelect);
    rlPopupWindows = new dhtmlXWindows();
    rlPopupWindows.setImagePath(webroot + "/UI/imgs/");
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
        x:20, y:30, width:260, height:260, center:true
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
        urlApiResultsFunction("Test Database Connection", cgi + "/testDBconnection", function(results){
	        rlStatusbar.setText("Connected to " + results["name"]);
        });
        win.close();
    })
}

function openFiling(onSelect, param1) {
    var filingId = null, win, layout, grid, form;
    win = rlPopupWindows.createWindow({
        id:"openFiling",
        x:20, y:30, width:864, height:400, center:true
        /*
	    onClose:function(){
	    	//layout.unload();
	    	//grid.unload();
	        return true;
	    }
	    */
    });
    // get previous filing selection parameters
    args = readCookie("rlFilingSelection");
    if (args && args.length >= 3) {
        args = Base64.decode(args).split('\t');
        selectFilingsUrl = cgi + "/grid/filings?filing=" + args[0] + "&name=" + args[1] + "&date=" + args[2] + "&sic=" + args[3] + "&formtype=" + args[4] + "&ticker=" + args[5];
    } else {
        args = new Array("", "", "", "", "", "");
        selectFilingsUrl = cgi + "/grid/filings";
    }
    win.setText("Select a filing to open");
    winToolbar = win.attachToolbar();
    winToolbar.setIconsPath(webroot + "/cli/images/");
    winToolbar.addButton("find", 0, null, "toolbarFind.gif", null);
    winToolbar.setItemToolTip("find", "click to show matching filings");
    winToolbar.addText("_filing", 1, "Nbr");
    winToolbar.addInput("filing", 2, args[0], 96);
    winToolbar.addText("_name", 3, "Name");
    winToolbar.addInput("name", 4, args[1], 232);
    winToolbar.addText("_tickerSymbol", 5, "Tkr");
    winToolbar.addInput("tickerSymbol", 6, args[5], 42);
    winToolbar.addText("_formType", 7, "Form");
    winToolbar.addInput("formType", 8, args[4], 42);
    winToolbar.addText("_date", 9, "Date");
    winToolbar.addInput("date", 10, args[2], 48);
    winToolbar.addText("_sic", 11, "SIC");
    winToolbar.addInput("sic", 12, args[3], 36);
    inputToolTip = 'Match with * and ? wildcards.  Search is case insensitive.  (End with * to match rest of value.)  If first character is ~ then the rest is a posix regex pattern (case insensitive).';
    winToolbar.setItemToolTip("filing", inputToolTip);
    winToolbar.setItemToolTip("name", inputToolTip);
    winToolbar.setItemToolTip("date", inputToolTip);
    winToolbar.setItemToolTip("sic", inputToolTip);
    winToolbar.attachEvent("onClick", function(id){
        if (id == "find") {
        	args = new Array(winToolbar.getValue("filing"),  winToolbar.getValue("name"), winToolbar.getValue("date"), winToolbar.getValue("sic"), winToolbar.getValue("formType"), winToolbar.getValue("tickerSymbol"));
	        createCookie("rlFilingSelection", Base64.encode(args.join('\t')), 365 * 5);
	        grid.clearAll();
		    grid.load(cgi + "/grid/filings?filing=" + args[0] + "&name=" + args[1] + "&date=" + args[2] + "&sic=" + args[3] + "&formtype=" + args[4] + "&ticker=" + args[5],
		              "json");
        } else
            alert("Toolbar button with name "+id+" was clicked");
    });
    grid = win.attachGrid();
    grid.setHeader("Filing,Name,Tckr Sym,Form Type,Timestamp,URL,SIC,Creation Software,Messages");
    grid.setInitWidths("132,148,42,42,124,48,36,64,400");
    grid.setColAlign("left,left,left,left,left,left,left,left,left");
    grid.setColTypes("ro,ro,ro,ro,ro,ro,ro,ro,ro");
    grid.setColSorting("str,str,str,str,str,str,str,str,str");
    if (onSelect == "openMultivariateGrid" || onSelect == "addToMultivariateGrid")
    	grid.enableMultiselect(true);
    grid.init();
    grid.setSkin(rlSkin);
    // context menu
    if (onSelect == "openMultivariateGrid" || onSelect == "addToMultivariateGrid") {
	    var gridCntxMenu = new dhtmlXMenuObject();
		gridCntxMenu.setIconsPath(webroot + "/cli/images/");
		gridCntxMenu.renderAsContextMenu();
		gridCntxMenu.attachEvent("onClick", function(menuItemId,type){ // context menu
	        var rowIDs = [];
	        if (menuItemId == 'open_all') {
	        	for (var i=0; i<grid.getRowsNum(); i++)
	        		rowIDs.push(grid.getRowId(i));
	        } else if (menuItemId == 'open_selected') {
	        	rowIDs = grid.getSelectedRowId().split(',');
	        } else if (menuItemId == 'open_clicked') {
	        	rowIDs.push(grid.contextID.split('_')[0]);
	        } else {
				return true;
		    }
	        win.close();
			if (onSelect == "openMultivariateGrid")
			    openMultivariateGrid(rowIDs);
			else if (onSelect == "addToMultivariateGrid")
			 	addToMultivariateGrid(rowIDs, param1);
			return true;
		});
		gridCntxMenu.loadStruct(webroot + "/cli/menuSelectMultivariateFilings.xml");
		grid.enableContextMenu(gridCntxMenu);
	} else {
	    grid.attachEvent("onRowSelect", function(id,ind){
	        win.close();
	    	setTimeout(function(){ 
	    				 if (onSelect == "openFiling")
	    				     viewObject('filing', id)
	    			  }, 200);
	        return true;
	    });
	}
    grid.load(selectFilingsUrl, "json");
    rlStatusbar.setText("Select a filing to view...");
}

function closeObjectView() {
	if (rlCurrentTabOrdinal in rlObjectViews) {
		var objectView = rlObjectViews[rlCurrentTabOrdinal];
		var tabItems = objectView['tabItems'];
		for (tabName in tabItems)
		if (tabItems.hasOwnProperty(tabName)) {
				var tabItem = tabItems[tabName];
				/* v 3.0
				tabItem['tabBar'].removeTab(tabItem['tabName'],true);
				*/
				tabItem['tabBar'].tabs(tabItem['tabName']).close();
				// tabItem['grid'].destructor();
			}
		delete rlObjectViews[rlCurrentTabOrdinal];
	}
}

function openDocument() {
    var win, layout, grid, form;
    win = rlPopupWindows.createWindow({
        id:"openDocument",
        x:20, y:30, width:800, height:400, center:true
        /*
	    onClose:function(){
	    	//layout.unload();
	    	//grid.unload();
	        return true;
	    }
	    */
    });
    // get previous filing selection parameters
    args = readCookie("rlDocumentSelection");
    if (args && args.length >= 3) {
        args = Base64.decode(args).split('\t');
        selectDocumentsUrl = cgi + "/grid/documents?documentUrl=" + args[0] + "&documentType=" + args[1] + "&namespace=" + args[2];
    } else {
        args = new Array("", "", "");
        selectDocumentsUrl = cgi + "/grid/documents";
    }
    win.setText("Select a document to open");
    winToolbar = win.attachToolbar();
    winToolbar.setIconsPath(webroot + "/cli/images/");
    winToolbar.addButton("find", 0, null, "toolbarFind.gif", null);
    winToolbar.setItemToolTip("find", "click to show matching documents");
    winToolbar.addText("_url", 1, "URL");
    winToolbar.addInput("url", 2, args[0], 132);
    winToolbar.addText("_type", 3, "Type");
    winToolbar.addInput("type", 4, args[1], 300);
    winToolbar.addText("_namespace", 5, "Namespace");
    winToolbar.addInput("namespace", 6, args[2], 64);
    inputToolTip = 'Match with * and ? wildcards.  Search is case insensitive.  (End with * to match rest of value.)  If first character is ~ then the rest is a posix regex pattern (case insensitive).';
    winToolbar.setItemToolTip("url", inputToolTip);
    winToolbar.setItemToolTip("type", inputToolTip);
    winToolbar.setItemToolTip("namespace", inputToolTip);
    winToolbar.attachEvent("onClick", function(id){
        if (id == "find") {
        	args = new Array(winToolbar.getValue("url"),  winToolbar.getValue("type"), winToolbar.getValue("namespace"));
	        createCookie("rlDocumentSelection", Base64.encode(args.join('\t')), 365 * 5);
	        grid.clearAll();
		    grid.load(cgi + "/grid/documents?documentUrl=" + args[0] + "&documentType=" + args[1] + "&namespace=" + args[2],
		              "json");
        } else
            alert("Toolbar button with name "+id+" was clicked");
    });
    grid = win.attachGrid();
    grid.setHeader("URL,Type,Namespace");
    grid.setInitWidths("320,160,320");
    grid.setColAlign("left,left,left");
    grid.setColTypes("ro,ro,ro");
    grid.setColSorting("str,str,str");
    grid.init();
    grid.setSkin(rlSkin);
    grid.attachEvent("onRowSelect", function(id,ind){
        win.close();
    	setTimeout(function(){
				      viewObject('document', id);
					}, 200);
        return true;
    });
    grid.load(selectDocumentsUrl, "json");
    rlStatusbar.setText("Select a document to view...");
}

function openMultivariateGrid(filingIds) {
	viewMultivariate(filingIds);
}


function onSelectObject(objectView, id, clickedTabName) {
	try {
		for (tabName in objectView.tabItems)
			if (objectView.tabItems.hasOwnProperty(tabName)) {
				var tabItem = objectView.tabItems[tabName];
				if (clickedTabName != tabItem.tabName && tabItem.showObjectFunction) {
					tabItem.showObjectFunction(tabItem.grid,
											   objectView.objectIdKey, 
											   objectView.objectId, 
											   id, 
											   tabItem.arcrole);
				}
		}
	} catch (err) {
		alert("Exception in onSelectObject for " + clickedTabName + "\n\nError: " + err.message);
	}
	return true;
}

function propertyGridShowObject(grid, viewObjectIdKey, viewObjectId, id) {
    grid.clearAll();
    
    grid.load(cgi + "/grid/properties?" + viewObjectIdKey + "=" + viewObjectId + "&id=" + id, 'json');
}

function treeGridShowObject(grid, viewObjectIdKey, viewObjectId, id, arcrole) {
    urlApiResultsFunction("Selecting relationships", 
                    	  cgi + "/select/relationships?id=" + id + "&" + 
                                viewObjectIdKey + "=" + viewObjectId + 
                                "&arcrole=" + arcrole, 
                          function(results){
    	var id = results[0];
    	grid.selectRowById(id);
	    grid.openItem(grid.getParentId(id));
		grid.showRow(id);
    });
}

function aspectsGridShowObject(grid, viewObjectIdKey, viewObjectId, id) {
    urlApiResultsFunction("Selecting aspects", 
    					  cgi + "/select/aspects?id=" + id, 
    					  function(results){
		grid.selectRowById(results[0], false, true, false);
    });
}

function dataPointsGridShowObject(grid, viewObjectIdKey, viewObjectId, id) {
    urlApiResultsFunction("Selecting data point", 
    					  cgi + "/select/datapoints?id=" + id + "&" + viewObjectIdKey + "=" + viewObjectId, 
    					  function(results){
        grid.selectRowById(results[0], false, true, false);
    });
}

function newGridItem(name, objectView, tabBar, width, colHeaders, colWidths, colAligns, multiline, colTypes, colSorts, contextMenu, arcrole, loadUrl, setInitialViewActive, onRowSelectFunction, showObjectFunction) {
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
	var _colTypes = colTypes;
	if (_colTypes.substr(0,7) == "tree-ro") {
		grid.enableTreeCellEdit(false);
		_colTypes = "tree" + _colTypes.substr(7);
    }
    grid.setColTypes(_colTypes);
    grid.setColSorting(colSorts);
    grid.setImagesPath(webroot + "/UI/imgs/");
    grid.setIconsPath(webroot + "/cli/images/");
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
  						onRowSelectFunction(objectView, id, tabName);
  						}, 300);
    	});
    }

    if (loadUrl && ('objectId' in objectView) && ('objectIdKey' in objectView)) {
    	loadUrl += "?" + objectView.objectIdKey + "=" + objectView.objectId;
    	if (arcrole)
    		loadUrl += "&arcrole=" + arcrole;
    }
	var gridObj = {
		grid: grid,
		name: name,
		tabBar: tabBar,
		tabName: tabName,
		objectId: objectView.objectId,
		loadUrl: loadUrl,
		arcrole: arcrole,
		setInitialViewActive: setInitialViewActive,
		showObjectFunction: showObjectFunction};

    objectView.tabItems[name] = gridObj;

    // context menu
    if (contextMenu) {
	    var gridCntxMenu = new dhtmlXMenuObject();
		gridCntxMenu.setIconsPath(webroot + "/cli/images/");
		gridCntxMenu.renderAsContextMenu();
		gridCntxMenu.attachEvent("onClick", function(menuItemId,type){ // context menu
	        var id = grid.contextID;
	        if (menuItemId == 'expand') {
	        	grid.expandAll();
	        } else if (menuItemId == 'collapse') {
	        	grid.collapseAll();
	        } else if (menuItemId == 'excel') {
	        	grid.toExcel(webroot + "/UI/grid-excel-php/generate.php");
	        } else if (menuItemId == 'pdf') {
	        	grid.toPDF(webroot + '/UI/grid-pdf-php/generate.php');
	        } else if (menuItemId == "remove_col" || menuItemId == "remove_row" || menuItemId == "add_row" ||
	                   menuItemId == "show_heatmap") {
	        	multiVariateMenuClick(menuItemId, id, objectView, name);
	        } else {
				return true;
		    }
		});
		gridCntxMenu.loadStruct(webroot + "/cli/" + contextMenu + ".xml");
		grid.enableContextMenu(gridCntxMenu);
		gridObj.gridCntxMenu = gridCntxMenu;
		gridObj.heatMap = false;
	}
}

function viewObject(objectType, objectId) {
	var isDocumentView = (objectType == 'document');
	var objectView = {
		objectIdKey: objectType + "Id", // e.g., filingId or documentId
		objectId: objectId,
	    tabItems: {} };
    rlStatusbar.setText("Loading " + objectType + " " + objectId);
	rlOpenOrdinal += 1;
	rlCurrentTabOrdinal = rlOpenOrdinal.toString();
	rlObjectViews[rlCurrentTabOrdinal] = objectView;
	if (objectType == 'filing') {
		// these panes are active for filing (otherwise isDocumentView sets properties, aspects, and pre LB active)
		newGridItem("Messages", objectView, rlTabbarBottom, 60,
					"Seq,Code,Level,Text",
					"32,180,120,600",
					"right,left,left,left", true,
					"ro,ro,ro,ro",
					"str,str,str,str",
					"menuObjectGrid",
					null, cgi + "/grid/messages", true, onSelectObject, null);
		newGridItem("Fact List", objectView, rlTabbarTopRight, 60,
					"Name,Line,ContextRef,Unit,Value",
					"200,60,100,80,200",
					"left,left,left,left,left", false,
					"ro,ro,ro,ro,ro",
					"str,str,str,str,str",
					"menuObjectGrid",
					null, cgi + "/grid/datapoints", true, onSelectObject, dataPointsGridShowObject);
		newGridItem("DTS", objectView, rlTabbarTopLeft, 32,
					"Document",
					"400",
					"left", false,
					"tree",
					"str",
					"menuObjectGrid",
					null, cgi + "/grid/DTS", true, null, null);
	}
	newGridItem("Properties", objectView, rlTabbarTopLeft, 72,
				"Property,Value",
				"100,200",
				"left,left", false,
				"tree-ro,ro",
				"str,str",
				"menuObjectGrid",
				null, null, isDocumentView, null, propertyGridShowObject);
    rlStatusbar.setText("Loading aspects " + objectId);
	newGridItem("Aspects", objectView, rlTabbarBottom, 60,
				"Label,Name,Period,Balance,Data Type,Base Type",
				"300,200,60,60,140,140",
				"left,left,left,left,left,left", false,
				"ro,ro,ro,ro,ro,ro",
				"str,str,str,str,str,str",
				"menuObjectGrid",
				null, cgi + "/grid/aspects", isDocumentView, onSelectObject, aspectsGridShowObject);
    rlStatusbar.setText("Loading linkbases " + objectId);
	newGridItem("Presentation", objectView, rlTabbarTopRight, 72,
				"Name,Type,References",
				"400,100,200",
				"left,left,left", false,
				"tree,ro,ro",
				"str,str,str",
				"menuObjectGrid",
				"http://www.xbrl.org/2003/arcrole/parent-child", 
				cgi + "/grid/relationships", isDocumentView, onSelectObject, treeGridShowObject);
	newGridItem("Calculation", objectView, rlTabbarTopRight, 68,
				"Name,Weight,Balance",
				"400,50,70",
				"left,right,left", false,
				"tree,ro,ro",
				"str,str,str",
				"menuObjectGrid",
				"http://www.xbrl.org/2003/arcrole/summation-item", 
				cgi + "/grid/relationships", false, onSelectObject, treeGridShowObject);
	newGridItem("Dimensions", objectView, rlTabbarTopRight, 72,
				"Name,Arcrole,Closed,Usable",
				"400,120,50,50",
				"left,left,left,left", false,
				"tree,ro,ro,ro",
				"str,str,str,str",
				"menuObjectGrid",
				"XBRL-dimensions", 
				cgi + "/grid/relationships", false, onSelectObject, treeGridShowObject);
    rlStatusbar.setText("");
    openTabItemGrids(objectView.tabItems);
}

function openTabItemGrids(tabItems, clearAll) {
	// load grids
	for (tabName in tabItems)
	    if (tabItems.hasOwnProperty(tabName)) {
			var tabItem = tabItems[tabName];
			if (tabItem['loadUrl']) {
				if (clearAll == true)
					tabItem.grid.clearAll();
				tabItem.grid.load(tabItem.loadUrl, "json");
				/* v 3.0
	            if (tabItem.setInitialViewActive)
					tabItem.tabBar.setTabActive(tabItem.tabName);
				*/
	            if (tabItem.setInitialViewActive)
					tabItem.tabBar.tabs(tabItem.tabName).setActive();
			} else {
				if (tabItem.setInitialViewActive)
					tabItem.tabBar.tabs(tabItem.tabName).setActive();
			}
		}
}

function onSelectMultivar(objectView, id, clickedTabName) {
	try {
		var colVariable = '';
		for (tabName in objectView.tabItems)
			if (objectView.tabItems.hasOwnProperty(tabName)) {
				var tabItem = objectView.tabItems[tabName];
				if (clickedTabName == tabItem.tabName) {
					var iCol = tabItem.grid.getSelectedCellIndex();
					if (iCol > 0)
						colVariable = tabItem.grid.getColLabel(iCol);
					break;
				}
			}
		for (tabName in objectView.tabItems)
			if (objectView.tabItems.hasOwnProperty(tabName)) {
				var tabItem = objectView.tabItems[tabName];
				if (clickedTabName != tabItem.tabName && tabItem.showObjectFunction) {
					tabItem.showObjectFunction(tabItem.grid,
											   objectView.objectIdKey, 
											   objectView.objectId, 
											   id, 
											   colVariable);
				}
		}
	} catch (err) {
		alert("Exception in onSelectMultivar for " + clickedTabName + "\n\nError: " + err.message);
	}
	return true;
}

function multivariateFilingShowObject(grid, viewObjectIdKey, viewObjectId, id, colVariable) {
    urlApiResultsFunction("Selecting Multivariate Filing", 
    					  cgi + "/select/multivariateFilings?filingId=" + id, 
    					  function(results){
        grid.selectRowById(results[0], false, true, false);
    });
}

function multivariateVariableShowObject(grid, viewObjectIdKey, viewObjectId, id, colVariable) {
    urlApiResultsFunction("Selecting Multivariate Variable", 
    					  cgi + "/select/multivariateRules?name=" + colVariable, 
    					  function(results){
        grid.selectRowById(results[0], false, true, false);
    });
}

function multivariateVariableShowProperties(grid, viewObjectIdKey, viewObjectId, id, colVariable) {
    grid.clearAll();    
    grid.load(cgi + "/view/multivariateProperties?filingId=" + id + "&name=" + colVariable, 'json');
}

function viewMultivariate(filingIds) {
	var objectView = {
		filingIds: filingIds,
		variables: ["SALE","COGS","GP","XSGA","XRD","EPSPI","EPSFI"],
		tabItems: {},
		heatMap: false
	};
	rlOpenOrdinal += 1;
	rlCurrentTabOrdinal = rlOpenOrdinal.toString();
	rlObjectViews[rlCurrentTabOrdinal] = objectView;
	newGridItem("Multivariate", objectView, rlTabbarTopRight, 80,
				"Filing",
				"200",
				"left", false,
				"ro",
				"str",
				"menuMultivariateGrid",
				null, cgi + "/grid/multivariateGrid?filingIds=" + objectView.filingIds.join(',') + 
							"&variables=" + objectView.variables.join(','),
				true, onSelectMultivar, null); //	dataMultivariateShowObject);
	newGridItem("Properties", objectView, rlTabbarTopLeft, 72,
				"Property,Value",
				"100,200",
				"left,left", false,
				"tree-ro,ro",
				"str,str",
				null,
				null, null, true, null, multivariateVariableShowProperties);
	newGridItem("Variables", objectView, rlTabbarBottom, 60,
				"Label,Name,Rule",
				"300,200,600",
				"left,left,left", false,
				"ro,ro,ro",
				"str,str,str",
				"menuVaribleRules",
				null, cgi + "/grid/multivariateRules?variables=" + objectView.variables.join(','), 
				true, onSelectObject, multivariateVariableShowObject);
	newGridItem("Filings", objectView, rlTabbarBottom, 60,
				"Filing,Name,Form,Timestamp,URL,SIC,Creation Software",
				"132,184,48,124,48,36,64",
				"left,left,left,left,left,left,left", false,
				"ro,ro,ro,ro,ro,ro,ro",
				"str,str,str,str,str,str,str",
				"menuVaribleRules",
				null, cgi + "/grid/multivariateFilings?filingIds=" + objectView.filingIds.join(','), 
				true, onSelectObject, multivariateFilingShowObject);
	
	// add variables columns
	var mvGrid = objectView.tabItems.Multivariate.grid;
	for (var iCol=0; iCol<objectView.variables.length; iCol+=1) {
		var colVar = objectView.variables[iCol];
		var nCol = mvGrid.getColumnsNum();
		mvGrid.insertColumn(nCol);
		mvGrid.setColWidth(nCol,100);
		mvGrid.setColLabel(nCol, objectView.variables[iCol]);
	}
	// load grids
    openTabItemGrids(objectView.tabItems);
}

function multiVariateMenuClick(menuItemId, id, objectView, name) {
	if (menuItemId == "remove_col") {
	} else if (menuItemId == "remove_row") {
		var rowId = objectView.tabItems.Multivariate.grid.contextID.split('_')[0];
		for (var i=0; i<objectView.filingIds.length; i++)
			if (objectView.filingIds[i].toString() == rowId) {
				objectView.filingIds.splice(i,1);
				refreshMultivariateLoadUris(objectView);
				openTabItemGrids(objectView.tabItems, true);
				break;
			}
	} else if (menuItemId == "add_row") {
		openFiling("addToMultivariateGrid", objectView);
	} else if (menuItemId == "show_heatmap") {
		cntxMenu = objectView.tabItems.Multivariate.gridCntxMenu;
		objectView.tabItems.Multivariate.heatMap = cntxMenu.getCheckboxState("show_heatmap");
		refreshMultivariateLoadUris(objectView);
		openTabItemGrids(objectView.tabItems, true);
	}
	// redraw grid
}

function addToMultivariateGrid(filingIds, objectView) {
	for (var i=0; i<filingIds.length; i++)
	    objectView.filingIds.push(filingIds[i]);
	refreshMultivariateLoadUris(objectView);
}

function refreshMultivariateLoadUris(objectView) {
	// refresh load URLs with new filing Ids
	objectView.tabItems.Multivariate["loadUrl"] = 
		cgi + "/grid/multivariateGrid?filingIds=" + objectView.filingIds.join(',') + 
							         "&variables=" + objectView.variables.join(',');
	if (objectView.tabItems.Multivariate.heatMap)
		objectView.tabItems.Multivariate["loadUrl"] += "&heatMap=true";
	objectView.tabItems.Filings["loadUrl"] = 
		cgi + "/grid/multivariateFilings?filingIds=" + objectView.filingIds.join(',');
	openTabItemGrids(objectView.tabItems, true);
}

function doTest(testId) {
	var objectView = {
		testId: testId,
		tabItems: {},
	};
	rlOpenOrdinal += 1;
	rlCurrentTabOrdinal = rlOpenOrdinal.toString();
	rlObjectViews[rlCurrentTabOrdinal] = objectView;
	var colHdg, colWidth, colAlign, colMode, colType;
	if (testId == "test_multivariate_COST2014sample") {
		colHdg = "Filing,CIK,COST";
		colWidth = "200,100,100";
		colAlign = "left,left,left";
		colMode = "ro,ro,ro";
		colType = "str,str,str";
	}
	newGridItem("TestCase", objectView, rlTabbarTopRight, 80,
				colHdg, colWidth, colAlign, false, colMode, colType,
				"menuTestResult",
				null, cgi + "/grid/testCase?testId=" + testId,
				true, null, null); 
	// load grids
    openTabItemGrids(objectView.tabItems);
}

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
