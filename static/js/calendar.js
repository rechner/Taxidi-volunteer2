/* ===============================
| CALENDAR.JS
| Copyright, Andy Croxall (mitya@mitya.co.uk)
| For documentation and demo see http://www.mitya.co.uk/scripts/Calendar-and-date-picker-95
|
| USAGE
| This script may be used, distributed and modified freely but this header must remain in tact.
| For usage info and demo, including info on args and params, see www.mitya.co.uk/scripts
=============================== */

(function() {

	//============== prep

	calendar = function(constrArgs) {
		for(var y in instances) if (instances[y] == constrArgs.callback_field) return false;
		instances.push(constrArgs.callback_field);
		this.initiate(constrArgs);
	}
	calendar.globals = {
	    months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
	    thiss: null
	}
	var instances = [];


	//============== config

	calendar.conf = {
	    general: { //table and global
		css: {zIndex: 100, borderCollapse: 'collapse'},
		  tableCellSpacing: 0,
		  emptySquaresFiller: '-',
	    },
	    monthNameHeader: { //month title
		css: {fontSize: '13px', color: '#fff', background: '#26a1ce'}
	    },
	    yearSelect: { //drop-down for picking year (yearSelect is passed in constructor args)
		css: {color: '#fff', background: '#26a1ce', border: 'solid 1px #009ad6', margin: '2px 0', padding: '0 4px', fontWeight: 'bold'}
	    },
	    weekdaysHeader: { //if arguments passed to calendar.initiate() allow it to be shown
		css: {fontSize: '12px', color: '#666', height: '25px'}
	    },
	    weekendDaysHeader: { //only take effect if arguments passed to calendar.initiate() allow it to be shown
		css: {}
	    },
	    dateCells: { //general styles for all dates
		css: {fontSize: '12px', background: '#f4f4f4', padding: '4px', border: 'solid 1px #ccc'},
		  click_css: {}
	    },
	    weekendDateCells: {
		css: {background: '#e8f6b2'}
		},
	    validDateCells: { //clickable dates only (if not restricting which dates are clickable via allowedDates or disallowedDate paramaters, this is ALL dates)
		css: {color: '#00659d', padding: '4px', fontWeight: 'bold'},
		css_hover: { background: '#ccc'}
		},
		invalidDateCells: { //non-clickable dates only
			css: {color: '#aaa'}
		},
	    arrows: { //month toggle arrows
		  css: {color: '#fff', background: '#26a1ce', padding: '0 0 4px 0', fontSize: 20},
		  hover_css: {color: '#111'},
		prevLabel: '&laquo;',
		nextLabel: '&raquo;'
	    }
	};


	//============== initialisation and construction of object

	calendar.prototype.initiate = function(constrArgs) {


		//prep

		var today = new Date();
		this.constrArgs = constrArgs;
		this.currMonthShowing = 0;
		this.currYearShowing = !this.allowYearSelect ? today.getFullYear() : constrArgs.yearSelect.end;
	    id = $('.calendar').length;
		ie = navigator.appVersion.match(/MSIE (\d{1})/);
		calendar.ie = ie ? ie[1] : false;
		this.alwaysVisible = !constrArgs.focusElements && !constrArgs.clickElements;
		var ddyyyyPattern = /\d{1,2}\/\d{4}/;
		var yyyyPattern = /\d{4}/;
		var smy_splitter = constrArgs.startMonthAndYear ? this.constrArgs.startMonthAndYear.split('/') : null;

		Date.prototype.monthsDiff = function(date) {
		    var months;
		    months = (date.getFullYear() - this.getFullYear()) * 12;
		    months -= this.getMonth();
		    months += date.getMonth();
		    return months;
		}


		//first check args passed are not conflictory

		var error = {prop: null, descr: null};

		//invalid start month/year format
		if (constrArgs.startMonthAndYear && !ddyyyyPattern.test(this.constrArgs.startMonthAndYear)) {
			error.prop = 'startMonthAndYear';
			error.descr = 'Invalid value - should be in dd/yyyy format';

		//year select range passed but...
		} else if (constrArgs.yearSelect) {

			//invalidly
			if (typeof constrArgs.yearSelect != 'object' || !yyyyPattern.test(constrArgs.yearSelect.start) || !yyyyPattern.test(constrArgs.yearSelect.end)) {
				error.prop = 'yearSelect';
				error.descr = 'start and/or end years in range not in valid yyyy format.';

			//also imposing futureOnly/pastOnly
			} else if (constrArgs.futureOnly || constrArgs.pastOnly)
				error.descr = 'You cannot pass a year select range AND impose pastOnly/futureOnly - this is contradictory.';

			//year select start year is not earlier than end year
			else if (constrArgs.yearSelect.start >= constrArgs.yearSelect.end) {
				error.prop = 'yearSelect';
				error.descr = 'Start date in year select range must be earlier than end date';

			//requested start year is outside range
			} else if (smy_splitter && (parseInt(smy_splitter[1]) > constrArgs.yearSelect.end || parseInt(smy_splitter[1]) < constrArgs.yearSelect.start)) {
				error.prop = 'startDateAndMonth';
				error.descr = "The start year you specified ("+smy_splitter[1]+") is outside the valid range of years specified ("+constrArgs.yearSelect.start+' - '+constrArgs.yearSelect.end+")";

			} else
				this.allowYearSelect = true;
		}

		if (error.descr) {
			alert("Calendar initialisation error\n\nAp instance: "+(id+1)+""+(error.prop ? "\n\nProperty: '"+error.prop+"'" : '')+"\n\n"+error.descr);
			return false;
		}


		//specific start month/year passed? If so, and is in valid format, pass month offset to build() so it doesn't default to current month, e.g.
		//if today is Jan 1st 2010 default request start date is '02/2011', offset is 13.

	    if (smy_splitter) {

		    var monthsOffset;

		  //work out months offset (i.e. difference) between current and requested start month. Note: +1 is because JS zero-indexes months

		  offsetYearAndMonth = smy_splitter[1]+''+smy_splitter[0];

		  var temp1 = new Date();
		  temp1.setDate(1);
		  var temp2 = new Date();
		  with (temp2) {
			  setFullYear(smy_splitter[1]);
			  setMonth(smy_splitter[0]-1);
			  setDate(1);
		}

		  monthsOffset = temp1.monthsDiff(temp2);

		}


		//build table

	    var t;
	    t =	"<table class='calendar' id='calendar_"+id+"'>";
	    t +=		"<thead>";
	    t +=			"<tr><th>"+calendar.conf.arrows.prevLabel+"<\/th><th colspan='5'><\/th><th>"+calendar.conf.arrows.nextLabel+"<\/th><\/tr>";
	    if (this.constrArgs.showDayHeadings)
		t += 		"<tr><th>M<\/th><th>T<\/th><th>W<\/th><th>Th<\/th><th>F<\/th><th>S<\/th><th>Su<\/th><\/tr>";
	    t += 		"<\/thead>";
	    t += 		"<tbody>";
	    t += 		"<\/tbody>";
	    t +=	"<\/table>";
	    document.write(t);
		this.table = $('#calendar_'+id);


		//scoping

		var thiss = this;


		//do stuff (remember that, before this code block runs, buildCalendar() and styleCalendarAndAddEvents() run first, called by this block's 1st line)

	    $(function() {

		  thiss.buildCalendar(!monthsOffset ? null : monthsOffset);

		  if (thiss.constrArgs.additionalCSS)
			thiss.table.css(thiss.constrArgs.additionalCSS);

		  if (thiss.constrArgs.highlightDayOnStart) {
			$('#startAsOn_'+thiss.table.attr('id')).css('borderColor', calendar.conf.dateCells.activeBorderColor);
			$('#startAsOn_'+thiss.table.attr('id')).addClass('on');
		  }


			//if neither clickEvents nor focusEvents passed, assume means to show calendar on load

			if (!thiss.alwaysVisible) {

				//else set calendar to appear/disappear on focus/click events as required.
				//live() ensures applies even to elements that don't exist yet if user is DOM-scripting

			  if (thiss.constrArgs.focusElements && !thiss.alwaysVisible) {
			    $(thiss.constrArgs.focusElements).addClass('focusElement'+thiss.table.attr('id')); //just so we can easily identify focus elements later
				$(thiss.constrArgs.focusElements).live('focusin', function() { thiss.wakeUp(); });
			    $(document).click(function(e) {

				  //don't disappear if click was to child of calendar or to focus element
				  if ($(e.target).parents('.calendar').length == 0 && !$(e.target).is('.focusElement'+thiss.table.attr('id'))) {
					thiss.cancelSleep = false;
					thiss.sleep();
				  }

			    });
			  }

			  if (thiss.constrArgs.clickElements)
				$(thiss.constrArgs.clickElements).live('click', function(e) { e.stopPropagation(); thiss.wakeUp(); });

		    }

	    });

	}


	//============== build calendar. &month is null (if so, assume current month) or otherwise offset from current month. if rebuilding, calendar not hidden.

	calendar.prototype.buildCalendar = function(month, rebuilding) {

	    //prep

	    var tempDate = new Date(); //used for date calculations that shouldn't affect the main date objects, e.g. to work out how many days in current month
	    this.currMonthShowing = !month ? 0 : month;
	    this.table.children('tbody').html(''); //clean up from any previous month


	    //establish a date object we can use for working with the requested month

	    this.dateObjToUseForThisMonth = new Date();


	    //set date in new object to 1 so it's workable for all months, otherwise it will assume today's date and if that's, say, 31, that will cause problems when dealing with months like Feb, Apr etc

	    this.dateObjToUseForThisMonth.setDate(1);
	    if (month) {
		  this.dateObjToUseForThisMonth.setMonth(this.dateObjToUseForThisMonth.getMonth() + month);
		  tempDate.setMonth(tempDate.getMonth() + month);
		  this.currYearShowing = tempDate.getFullYear();
	    }


	    //ascertain number of days in this month

	    tempDate.setDate(32);
	    var numDaysInThisMonth = 32 - tempDate.getDate();


	    //store the month, plus work out the TD offset to start putting dates in depending on day of week of 1st of this month (e.g. if Weds, offset is 2)

	    var monthToUse = this.dateObjToUseForThisMonth.getMonth();
	    this.dateObjToUseForThisMonth.setDate(1);
	    var tdOffset = this.dateObjToUseForThisMonth.getDay();


		//do year as text or as drop-down? (depends on whether 'allowYearSelect' passed)

		if (this.allowYearSelect) {
			var yearHTML =	"<select style='font-size: inherit; float: none'>";
			with(this.constrArgs.yearSelect) { for(var k = end; k>=start; k--) yearHTML += "<option"+(k == this.currYearShowing ? " selected='selected'" : '')+" >"+k+"</option>"; }
			yearHTML +=	"</select>";
		} else
			var yearHTML = this.dateObjToUseForThisMonth.getFullYear();


	    //write current month at top of table

	    this.table.find('thead tr:first-child th:nth-child(2)').html("<span style='line-height: 25px; color: inherit; font-size: inherit'>"+calendar.globals.months[monthToUse]+"</span> "+yearHTML);


		//put out actual date <td>s

	    var newTR, newTD;
	    for(var u=0; u<numDaysInThisMonth+(this.constrArgs.showDayHeadings ? tdOffset-1 : 0); u++) {


		//modulus - new <tr>?

		  if (u == 0 || !(u % 7)) {
			if (newTR != undefined)
			    this.table.children('tbody').get(0).appendChild(newTR); //new tr after every 7 TDs
			newTR = document.createElement('tr');
		  }


		  //create <td> and deal with it. Note we use UID so no conflicts with other instances of calendar()

		  newTD = document.createElement('td');
		  if (u == this.constrArgs.highlightDayOnStart-1+tdOffset-1) newTD.id = 'startAsOn_'+this.table.attr('id');
		  var text = u >= (this.constrArgs.showDayHeadings ? tdOffset-1 : 0) ? (u+1) - (this.constrArgs.showDayHeadings ? tdOffset-1 : 0) : '-';


		  //does allowedDates / disallowedDates require that this date isn't clickable? If so, store this fact in @title attribute

		  var	month = this.dateObjToUseForThisMonth.getMonth()+1,
		  		thisDatePieces = [this.dateObjToUseForThisMonth.getFullYear(), (month < 10 ? '0' : null)+month, (text < 10 ? '0' : null)+text],
		  		allowedDatesForThisYear = !this.constrArgs.allowedDates ? null : this.constrArgs.allowedDates[thisDatePieces[0]],
		  		disallowedDatesForThisYear = !this.constrArgs.disallowedDates ? null : this.constrArgs.disallowedDates[thisDatePieces[0]];
		  
		  if (typeof this.constrArgs.allowedDates == 'object' && allowedDatesForThisYear) {
			if (!in_array(thisDatePieces[2], allowedDatesForThisYear[thisDatePieces[1]])) newTD.title = 'disabled';
		  } else if (typeof this.constrArgs.disallowedDates == 'object') {
			if (in_array(thisDatePieces[2], disallowedDatesForThisYear[thisDatePieces[1]])) newTD.title = 'disabled';
		}


		  //off we go

		  newTD.appendChild(document.createTextNode(text));
		  newTR.appendChild(newTD);

	    }
	    if (newTR != undefined) this.table.children('tbody').get(0).appendChild(newTR);


	    //apply styling and events (do it here, not onload, otherwise <tbody> loses both when repopulated)

	    this.styleCalendarAndAddEvents(rebuilding);

	}


	//============== style table and add events (do it here rather than in CSS so we keep this all neat inside just one file, no dependencies)

	calendar.prototype.styleCalendarAndAddEvents = function(rebuilding) {


	    //shortcuts

	    var tds = this.table.find('td');
	    var validTds = tds.not(':contains('+calendar.conf.general.emptySquaresFiller+')').not('[title=disabled]');
	    var tdsAndThs = this.table.find('th, td');
	    var arrows = this.table.find('thead tr:first-child th:first-child, thead tr:first-child th:last-child');
	    var dayHeadings = this.table.find('thead tr:nth-child(2) th');


	    //scoping

	    var thiss = this;


	    //table & general

	    this.table.css(calendar.conf.general.css);
	    if (!rebuilding && !this.alwaysVisible) this.table.hide();
	    this.table.attr('cellspacing', calendar.conf.general.tableCellSpacing); //cellpadding
	    tdsAndThs.css('padding', calendar.conf.general.padding); //global padding


	    //month header

	    var mh;
	    (mh = this.table.find('thead tr:first-child th')).css(calendar.conf.monthNameHeader.css);
	    mh.css({textTransform: 'capitalize', padding: '2px 0'});


	    //year select drop-down (if exists)

	    var ysdd;
	    (ysdd = mh.children('select')).css(calendar.conf.yearSelect.css);
	    ysdd.css({position: 'relative', top: 1});
	    ysdd.change(function() {
		var selYear = parseInt($(this).children('option:selected').text());
		var diffBetweenSelAndCurrYears = Math.abs(thiss.currYearShowing - selYear);
		var monthsOffset = diffBetweenSelAndCurrYears * 12;
		var offset = selYear > thiss.currYearShowing ? thiss.currMonthShowing + monthsOffset : thiss.currMonthShowing - monthsOffset;
		thiss.buildCalendar(offset, true);
		});


	    //days of week header

	    dayHeadings.css(calendar.conf.weekdaysHeader.css);

	    if (thiss.constrArgs.showDayHeadings)
		dayHeadings.slice(5).css(calendar.conf.weekendDaysHeader.css);


	    //date cells

	    tds.css(calendar.conf.dateCells.css);
	    tds.css(calendar.conf.invalidDateCells.css);
	    tds.css({
		  textAlign: 'center',
		  cursor: 'pointer',
		  border: calendar.conf.dateCells.css.border ? calendar.conf.dateCells.css.border : 'solid 1px transparent'
	    });


		//valid tds

		validTds.css(calendar.conf.validDateCells.css);

	    if (thiss.constrArgs.showDayHeadings)
		this.table.find('td').filter(function() { return $(this).prevAll('td').length >= 5}).css(calendar.conf.weekendDateCells.css);

	    validTds.mouseover(function() {
		  if (!$(this).is('.on')) $(this).css(calendar.conf.validDateCells.css_hover); //day cells hover (border)
	    });
	    validTds.mouseout(function() {
		  if (!$(this).is('.on')) {
			$(this).css($(this).prevAll('td').length < 5 ? calendar.conf.dateCells.css : calendar.conf.weekendDateCells.css);
			$(this).css(calendar.conf.validDateCells.css);
		}
	    });


	    //when date selected

	    validTds.click(function() {

		//visual stuff
		  validTds.filter('.on').css('borderColor', 'transparent');
		  validTds.removeClass('on');
		  $(this).addClass('on');
		  $(this).css('borderColor', calendar.conf.dateCells.activeBorderColor);

		  //ascertain date relating to clicked TD (returns in format d(d)/m(m)/yyyy
		  thiss.dateObjToUseForThisMonth.setDate($(this).text());
		  var dateSelected = [];
		  dateSelected.push(thiss.dateObjToUseForThisMonth.getDate());
		  var month = thiss.dateObjToUseForThisMonth.getMonth();
		  dateSelected.push(!thiss.constrArgs.monthAsWord ? month + 1 : thiss.dateObjToUseForThisMonth.toString().split(' ')[1]);
		  dateSelected.push(thiss.dateObjToUseForThisMonth.getFullYear());
		  if (!thiss.constrArgs.noLeadingZeros) { for(var f in dateSelected) if (dateSelected[f] < 10) dateSelected[f] = '0'+dateSelected[f]; }
		  if (!thiss.constrArgs.datePartsAsArray) dateSelected = dateSelected.join('/');


		  //callback - see argument comments in initiate() for what can happen here. If callback_url, only do that. otherwise, any or all of other 3 can happen.

		  if (thiss.constrArgs.callback_url) {


			//check relevent tokens exist in url. Allow lack of %d, as may want to only pass year and month, not specific day. Replace tokens with date parts.

			var tokens = {d: dateSelected[0], m: dateSelected[1], y: dateSelected[2]};
			var goAhead = true;
			var url = thiss.constrArgs.callback_url;
			for(var c in tokens) {
				if (thiss.constrArgs.callback_url.indexOf('%'+c) == -1 && c != 'd') {
					goAhead = false; break;
				} else url = url.replace('%'+c, tokens[c]);
			  }
			  if (goAhead == true) location.href = url;

		} else {
			var field_val = thiss.constrArgs.callback_func ? thiss.constrArgs.callback_func.apply(this, $.merge(dateSelected.split('/'), [dateSelected])) : dateSelected;
			if(thiss.constrArgs.callback_field) $(thiss.constrArgs.callback_field).val(field_val);
			if(thiss.constrArgs.callback_var) eval(thiss.constrArgs.callback_var+' = dateSelected;');
		}


		    //lastly, make sure calendar sleeps (if not always visible) after this, as we've picked a date now

		    if (!thiss.alwaysVisible) {
				thiss.cancelSleep = false;
				thiss.sleep();
			}

	    });


	    //arrows - look

	    arrows.css(calendar.conf.arrows.css);
	    arrows.css({'cursor': 'pointer'});


	    //arrows - clicks (can't tidy this up anymore as anything but this records multiple clicks on arrows, bizarrely, meaning we jump multiple months).
	    //If pastOnly/futureOnly restrict access to past/future, arrows won't work if attempting this. Also, if year select range passed, won't allow you
	    //to go to dates outside this range

	    arrows.get(0).onclick = function(e) {
		  !window.event ? e.stopPropagation() : window.event.cancelBubble = true;
		  thiss.cancelSleep = true;
		  if ((thiss.currMonthShowing > 0 || !thiss.constrArgs.futureOnly) && ((thiss.allowYearSelect && thiss.constrArgs.yearSelect.start < thiss.currYearShowing) || !thiss.allowYearSelect)) {
			thiss.buildCalendar(thiss.currMonthShowing - 1, true);}
	    };
	    arrows.get(1).onclick = function(e) {
		  !window.event ? e.stopPropagation() : window.event.cancelBubble = true;
		  thiss.cancelSleep = true;
		  if ((thiss.currMonthShowing < 0 || !thiss.constrArgs.pastOnly) && ((thiss.allowYearSelect && thiss.constrArgs.yearSelect.end > thiss.currYearShowing) || !thiss.allowYearSelect))
			thiss.buildCalendar(thiss.currMonthShowing + 1, true);
	    }

	    arrows.mouseover(function() {
		if (!thiss.arrowOrigCol) thiss.arrowOrigCol =  $(this).css('color');
		  $(this).css(calendar.conf.arrows.hover_css);
	    });
	    arrows.mouseout(function() {
		  $(this).css('color', thiss.arrowOrigCol);
		  $(this).css(calendar.conf.arrows.css);
	    });


	    /*
	    hide calendar on document click, unless
		1) it is set to be always visible (from page load)
		2) the click was on an element registered as waking up the calendar on focus. (i.e. the same click event shouldn't both wake it up and hide it)
	    Note, clicks to calendar arrows aren't registered here; they don't propagate, as they clearly shouldn't cause the calendar to hide
	    */

	    if (!thiss.alwaysVisible) {

		  $(document).click = function(ev) {

			thiss.cancelSleep = false;
			var dontHide;

			arrows.each(function() {
			    if (this == ev.target) { dontHide = true; return false; }
			});
			if (thiss.constrArgs.focusElements) {
			    $(thiss.constrArgs.focusElements).each(function() {
				    if (this == ev.target) { dontHide = true; return false; }
			    });
			    }

			if (thiss.table.is(':visible') && !dontHide) thiss.sleep();

		  };
	    }

	}


	//============== interaction methods & utilities

	calendar.prototype.wakeUp = function() {
	    this.table.fadeIn();
	}

	calendar.prototype.sleep = function() {
	    if (!this.cancelSleep) this.table.fadeOut();
	}

	function in_array(needle, haystack, returnIndexNotKeyName) {
	    var counter = 0;
		if (needle && haystack instanceof Array) {
			for(var e in haystack) {
				if (haystack[e] == needle) { return !returnIndexNotKeyName ? e : counter; break; }
				counter++;
			}
		}
	};

})();
