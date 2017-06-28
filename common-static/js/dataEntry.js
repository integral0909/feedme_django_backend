(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
FormModal = require('./modules/formModal.js').FormModal,

DE = {
  init: function () {
    this.FormModal = new FormModal()
  },
  pageManagers: {
    Restaurant: require('./modules/pagemanagers/restaurant.js').Restaurant,
    Blog: require('./modules/pagemanagers/blog.js').Blog,
    Dish: require('./modules/pagemanagers/dish.js').Dish
  }
}

},{"./modules/formModal.js":3,"./modules/pagemanagers/blog.js":5,"./modules/pagemanagers/dish.js":6,"./modules/pagemanagers/restaurant.js":7}],2:[function(require,module,exports){
"use strict";
/// <reference path="./../../node_modules/@types/jquery/index.d.ts" />
exports.__esModule = true;
var FormManager = (function () {
    function FormManager() {
        var _this = this;
        this.formSelector = 'form.async-managed';
        this.callbackRegister = {};
        this.handleSubmit = function (e) {
            e.preventDefault();
            var $form = $(event.target).closest('form');
            var action = $form.attr('action');
            $.ajax({
                url: action,
                data: $form.serializeArray(),
                type: $form.attr('method')
            }).done(function (response) { return $form.replaceWith(response); })
                .done(function () { return _this.runCallbacks(action); });
        };
        this.runCallbacks = function (action) {
            try {
                var funcs = _this.callbackRegister[action];
                if (funcs !== undefined) {
                    for (var i = 0; i < funcs.length; i++) {
                        try {
                            funcs[i]();
                        }
                        catch (e) {
                            console.error(e);
                        }
                    }
                }
            }
            catch (e) {
                console.error(e);
            }
        };
        $('body').on('submit', this.formSelector, this.handleSubmit);
    }
    FormManager.prototype.registerCallback = function (id, func) {
        if (this.callbackRegister[id] !== undefined) {
            this.callbackRegister[id].push(func);
        }
        else {
            this.callbackRegister[id] = [func];
        }
    };
    return FormManager;
}());
exports.FormManager = FormManager;

},{}],3:[function(require,module,exports){
"use strict";
/// <reference path="./../../node_modules/@types/jquery/index.d.ts" />
exports.__esModule = true;
var FormModal = (function () {
    function FormModal(options) {
        var _this = this;
        this.element = $("<div id='FormModal' style='display:none;'><div class='pull-right' id='modal-x'>X</div><div id='modal-body'></div></div>");
        this.background = $("<div id='bg-overlay' style='display:none;'></div>");
        this.open = false;
        this.clickSelector = 'a[data-modal-open="form"]';
        this.toggleModal = function (event) {
            event.preventDefault();
            event.stopPropagation();
            var formUrl = $(event.target).closest(_this.clickSelector).data('formUrl');
            if (_this.open) {
                _this.hideModal();
            }
            else {
                _this.loadForm(formUrl);
            }
        };
        this.showModal = function () {
            _this.open = true;
            _this.background.fadeIn(300);
            _this.element.show(300);
        };
        this.hideModal = function () {
            _this.open = false;
            _this.background.fadeOut(300);
            _this.element.hide(300);
        };
        this.submit = function (e) {
            e.preventDefault();
            $.ajax({
                url: _this.form.attr('action'),
                data: _this.form.serializeArray(),
                type: _this.form.attr('method')
            }).done(function (response) { return _this.modalBody.html(response); })
                .done(function (response) { return _this.activeForm.success(response); })
                .fail(function () { return _this.activeForm.failure(); });
        };
        if (options !== undefined) {
            if (options.element !== undefined) {
                this.element = options.element;
            }
            if (options.clickSelector !== undefined) {
                this.clickSelector = options.clickSelector;
            }
        }
        this.modalBody = this.element.find('#modal-body');
        $('body').append(this.element);
        $('body').append(this.background);
        $('body').on('click', this.clickSelector, this.toggleModal);
        this.background.click(this.hideModal);
        $('#modal-x', this.element).click(this.hideModal);
        this.element.on('submit', 'form', this.submit);
    }
    FormModal.prototype.loadForm = function (formUrl) {
        var _this = this;
        this.modalBody.load(formUrl, function () {
            _this.form = _this.element.find('form');
            _this.showModal();
        });
    };
    return FormModal;
}());
exports.FormModal = FormModal;

},{}],4:[function(require,module,exports){
"use strict";
/// <reference path="./../../node_modules/@types/jquery/index.d.ts" />
exports.__esModule = true;
var FormsetManager = (function () {
    function FormsetManager(options) {
        var _this = this;
        this.delClickSelector = '.formset-delete-btn';
        this.delCheckWrapperSelector = '.formset-delete-cx';
        this.deleteForm = function (event) {
            event.preventDefault();
            event.stopPropagation();
            var $chck = $(event.target).siblings(_this.delCheckWrapperSelector).find('input');
            $chck.click();
            $(event.target).closest('.row').hide(300);
        };
        if (options !== undefined) {
            if (options.delClickSelector !== undefined) {
                this.delClickSelector = options.delClickSelector;
            }
            if (options.delCheckWrapperSelector !== undefined) {
                this.delCheckWrapperSelector = options.delCheckWrapperSelector;
            }
        }
        $('body').on('click', this.delClickSelector, this.deleteForm);
    }
    return FormsetManager;
}());
exports.FormsetManager = FormsetManager;

},{}],5:[function(require,module,exports){
"use strict";
/// <reference path="./../../../node_modules/@types/jquery/index.d.ts" />
exports.__esModule = true;
var FormManager_1 = require("./../FormManager");
var Blog = (function () {
    function Blog() {
        this.formManager = new FormManager_1.FormManager();
    }
    return Blog;
}());
exports.Blog = Blog;

},{"./../FormManager":2}],6:[function(require,module,exports){
"use strict";
/// <reference path="./../../../node_modules/@types/jquery/index.d.ts" />
exports.__esModule = true;
var FormManager_1 = require("./../FormManager");
var Dish = (function () {
    function Dish() {
        this.formManager = new FormManager_1.FormManager();
    }
    return Dish;
}());
exports.Dish = Dish;

},{"./../FormManager":2}],7:[function(require,module,exports){
"use strict";
/// <reference path="./../../../node_modules/@types/jquery/index.d.ts" />
exports.__esModule = true;
var formsetManager_1 = require("./../formsetManager");
var FormManager_1 = require("./../FormManager");
var Restaurant = (function () {
    function Restaurant() {
        var _this = this;
        this.timers = {};
        this.geocodeAddress = function () {
            _this.tzInput.prop("disabled", true);
            _this.suburbInput.prop("disabled", true);
            if (_this.timers.addr !== undefined) {
                clearTimeout(_this.timers.addr);
            }
            _this.timers.addr = setTimeout(function () {
                $.getJSON('/api/geocode/?address=' + _this.addrInput.val(), function (d) {
                    _this.suburbInput.val(d.suburb);
                    _this.suburbInput.prop("disabled", false);
                    _this.latitudeInput.val(d.latitude);
                    _this.longitudeInput.val(d.longitude);
                    $.getJSON('/api/geocode/?coords=' + d.latitude + ',' + d.longitude + '&return=timezone', function (d) {
                        _this.tzInput.val(d.timeZoneId);
                        _this.offsetMinutesInput.val(d.rawOffset / 60);
                        _this.tzInput.prop("disabled", false);
                    });
                });
            }, 1000);
        };
        this.addrInput = $('#id_address');
        this.tzInput = $('#id_timezone');
        this.offsetMinutesInput = $('#id_time_offset_minutes');
        this.suburbInput = $('#id_suburb');
        this.latitudeInput = $('#id_latitude');
        this.longitudeInput = $('#id_longitude');
        this.addrInput.on('input', this.geocodeAddress);
        this.formset = new formsetManager_1.FormsetManager();
        this.formManager = new FormManager_1.FormManager();
        this.formManager.registerCallback('/data-entry/forms/restaurants/', function () {
            var id = $("input[name=\"id\"]", '#restaurant-form').val();
            if (id > 0 && window.location.pathname !== '/data-entry/restaurants/' + id + '/change/') {
                window.location.assign('/data-entry/restaurants/' + id + '/change/');
            }
        });
        this.formManager.registerCallback('/data-entry/forms/blogs/', function () {
            $('#existing-blogs').load(window.location.pathname + ' #existing-blogs');
        });
        this.formManager.registerCallback('/data-entry/forms/dishes/', function () {
            $('#existing-dishes').load(window.location.pathname + ' #existing-dishes');
        });
        this.formManager.registerCallback('/data-entry/forms/recipes/', function () {
            $('#existing-recipes').load(window.location.pathname + ' #existing-recipes');
        });
    }
    return Restaurant;
}());
exports.Restaurant = Restaurant;

},{"./../FormManager":2,"./../formsetManager":4}]},{},[1]);
