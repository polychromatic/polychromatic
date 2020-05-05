/**
 * @category  html5 widgets
 * @package   Kelly
 * @author    Rubchuk Vladimir <torrenttvi@gmail.com>
 * @copyright 2015-2019 Rubchuk Vladimir
 * @license   GPLv3
 * @version   1.20
 *
 * Usage example :
 *
 *   new KellyColorPicker({place : 'color-picker'});
 *
 * ToDo :
 * 
 * Add switch color in colorsavers button (analog of X button in Photoshop)
 *
 **/

/**
 * Create color picker
 * @param {Array} cfg
 * @returns {KellyColorPicker}
 */

function KellyColorPicker(cfg) {
    var PI = Math.PI;

    var svFig; // current method SV figure object

    var changeCursor = true;

    var svCursor = new Object;
    svCursor.radius = 4;

    var canvas = false;
    var ctx = false;

    var method = 'quad';
    var alpha = false;          // is alpha slider enabled
    var drag = false;
    var cursorAnimReady = true; // sets by requestAnimationFrame to limit FPS on events like mousemove etc. when draging 

    var events = new Array();
    var userEvents = new Array();

    var canvasHelper = document.createElement("canvas");
    var canvasHelperCtx = false; // used if needed to copy image data throw ctx.drawImage for save alpha channel
    var rendered = false;        // is colorpicker rendered (without side alpha bar and cursors, rendered image stores in canvasHelperData
    var canvasHelperData = null; // rendered interface without cursors and without alpha slider [wheelBlockSize x wheelBlockSize]

    var input = false;

    // used by updateInput() function if not overloaded by user event
    var inputColor = true;     // update input color according to picker
    var inputFormat = 'mixed'; // text format of colorpicker color displayed in input element | values : mixed | hex | rgba

    var popup = new Object;    // popup block for input
    popup.tag = false;         // Dom element if popup is enabled
    popup.margin = 6;          // margin from input in pixels

    // container, or canvas element
    var place = false;
    var handler = this;

    var basePadding = 2;

    var padding;
    var wheelBlockSize = 200;
    var center;

    // current color
    var hsv;
    var rgb;
    var hex = '#000000';
    var a = 1;

    var resizeWith = false;
    var resizeSide = false;

    var colorSavers = new Array();

    var styleSwitch = false; // change method from square to triangle
    var svFigsPool = new Array(); // if we have button for switch method, better store already created figure object to buffer

    // style switch from triange to quad and backwards
    function initStyleSwitch() {

        styleSwitch = new Object;
        styleSwitch.size;
        styleSwitch.sizePercentage = 10;
        styleSwitch.position;
        styleSwitch.paddingY = 4;
        styleSwitch.paddingX = 4;
        styleSwitch.imageData = new Array();
        styleSwitch.lineWidth = 2;
        styleSwitch.color = '#c1ebf5';

        styleSwitch.updateSize = function () {
            this.size = parseInt(wheelBlockSize - (wheelBlockSize / 100) * (100 - this.sizePercentage));

            if (this.size < 16)
                this.size = 16;

            this.position = {x: this.paddingX, y: this.paddingY};
        }

        styleSwitch.draw = function () {

            if (this.imageData[method]) {
                ctx.putImageData(this.imageData[method], this.position.x, this.position.y);
                return;
            }

            var rgb = hexToRgb(this.color);

            canvasHelper.width = this.size;
            canvasHelper.height = this.size;

            canvasHelperCtx.clearRect(0, 0, this.size, this.size);
            canvasHelperCtx.beginPath();

            var switchFig = 'triangle';
            if (method == 'triangle')
                switchFig = 'quad';

            canvasHelperCtx.beginPath();

            if (this.size < 35) {
                var circleRadiusMain = canvasHelper.width / 2;
                var circleRadius = circleRadiusMain;
            } else {

                var circleRadiusMain = (canvasHelper.width / 2) - this.lineWidth;

                canvasHelperCtx.arc(this.size / 2, this.size / 2, circleRadiusMain, 0, PI * 2);
                canvasHelperCtx.strokeStyle = 'rgba(0, 0, 0, 0.4)';
                canvasHelperCtx.lineWidth = this.lineWidth;
                canvasHelperCtx.stroke();

                var circleRadius = circleRadiusMain - 6;
                canvasHelperCtx.closePath();
                canvasHelperCtx.beginPath();
                canvasHelperCtx.arc(this.size / 2, this.size / 2, circleRadius, 0, PI * 2);
                canvasHelperCtx.strokeStyle = 'rgba(0, 0, 0, 0.4)';
                canvasHelperCtx.lineWidth = this.lineWidth;
                canvasHelperCtx.stroke();
                canvasHelperCtx.closePath();
            }

            canvasHelperCtx.beginPath();
            var svmSize;

            if (switchFig == 'quad') {
                var workDiametr = (circleRadius * 2) - 4; // may be some paddings here
                svmSize = Math.floor(workDiametr / Math.sqrt(2));
                var padding = (this.size - svmSize) / 2;
                var svmPos = {x: padding + svmSize, y: padding + svmSize / 2}; // start middle point
                svmPos.y = svmPos.y - (svmSize / 2);
                canvasHelperCtx.moveTo(svmPos.x, svmPos.y); // right top
                canvasHelperCtx.lineTo(svmPos.x - svmSize, svmPos.y);  // left tp
                canvasHelperCtx.lineTo(svmPos.x - svmSize, svmPos.y + svmSize); // left bottom
                canvasHelperCtx.lineTo(svmPos.x, svmPos.y + svmSize); // right bottom

            } else {
                svmSize = Math.floor((2 * circleRadius - 4) * Math.sin(toRadians(60))); // side size
                var svmPos = {x: circleRadius * 2 + (circleRadiusMain - circleRadius), y: this.size / 2}; // start middle point
                var h = ((Math.sqrt(3) / 2) * svmSize);
                canvasHelperCtx.moveTo(svmPos.x, svmPos.y);
                canvasHelperCtx.lineTo(svmPos.x - h, svmPos.y - (svmSize / 2)); // top 
                canvasHelperCtx.lineTo(svmPos.x - h, svmPos.y + (svmSize / 2)); // bottom
                canvasHelperCtx.lineTo(svmPos.x, svmPos.y);
            }

            canvasHelperCtx.lineTo(svmPos.x, svmPos.y);


            canvasHelperCtx.fillStyle = 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ', 1)';
            canvasHelperCtx.fill();
            canvasHelperCtx.lineWidth = this.lineWidth;
            canvasHelperCtx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
            canvasHelperCtx.stroke();
            canvasHelperCtx.closePath();


            this.imageData[method] = canvasHelperCtx.getImageData(0, 0, canvasHelper.width, canvasHelper.width);
            ctx.drawImage(canvasHelper, this.position.x, this.position.y);

        }

        styleSwitch.isDotIn = function (dot) {
            if (
                    dot.x >= this.position.x && dot.x <= this.position.x + this.size &&
                    dot.y >= this.position.y && dot.y <= this.position.y + this.size
                    ) {
                return true;
            }

            //if (Math.pow(this.position.x - dot.x, 2) + Math.pow(this.position.y - dot.y, 2) < Math.pow(this.outerRadius, 2)) {
            //	return true;
            //}			

            return false;
        }
    }

    // triangle colorsavers for left and right side
    function initColorSaver(align, selected, color) {

        if (!selected)
            selected = false;
        else
            selected = true;

        var colorSaver = new Object;
        colorSaver.width; // size of side of triangle
        colorSaver.widthPercentage = 22;

        colorSaver.imageData = null; // last rendered colorsaver image
        colorSaver.align = align;
        colorSaver.selected = selected; // current color
        colorSaver.color = '#ffffff'; // hex color
        colorSaver.position; // top point of triangle
        colorSaver.paddingY = -4;
        colorSaver.paddingX = 4;
        colorSaver.lineWidth = 1;
        colorSaver.selectSize = 4;

        if (align == 'right') {
            colorSaver.paddingX = colorSaver.paddingX * -1;
        }

        if (colorSaver.selected) {
            colorSaver.color = hex;
        }

        if (color) {
            colorSaver.color = color;
        }

        colorSaver.updateSize = function () {
            this.width = parseInt(wheelBlockSize - (wheelBlockSize / 100) * (100 - this.widthPercentage));

            // start render point in global canvas coords
            if (this.align == 'left') {
                this.position = {x: 0, y: wheelBlockSize - this.width};
            } else if (this.align == 'right') {
                this.position = {x: wheelBlockSize - this.width, y: wheelBlockSize - this.width};
            }
        }

        // calc triangle area (same method as for triangle sv figure)
        colorSaver.calcS = function (p) {
            return Math.abs((p[1].x - p[0].x) * (p[2].y - p[0].y) - (p[2].x - p[0].x) * (p[1].y - p[0].y)) / 2;
        }

        colorSaver.isDotIn = function (dot) {

            var path = new Array();

            if (this.align == 'left') {
                path[0] = {x: this.position.x, y: this.position.y}; // top 
                path[1] = {x: this.position.x, y: this.position.y + this.width}; // bottom left
                path[2] = {x: this.position.x + this.width, y: this.position.y + this.width}; // bottom right
            } else {
                path[0] = {x: this.position.x + this.width, y: this.position.y}; // top 
                path[1] = {x: path[0].x, y: path[0].y + this.width}; // bottom right
                path[2] = {x: path[0].x - this.width, y: this.position.y + this.width}; // bottom left				
            }

            for (var i = 0; i <= path.length - 1; ++i)
            {
                path[i].x += this.paddingX;
                path[i].y += this.paddingY;
            }

            var selfS = this.calcS(path);

            var t = [
                {x: path[0].x, y: path[0].y},
                {x: path[1].x, y: path[1].y},
                {x: dot.x, y: dot.y}
            ];

            var s = this.calcS(t);
            t[1] = {x: path[2].x, y: path[2].y};
            s += this.calcS(t);
            t[0] = {x: path[1].x, y: path[1].y};
            s += this.calcS(t);

            if (Math.ceil(s) == Math.ceil(selfS))
                return true;
            else
                return false;
        }

        colorSaver.draw = function () {

            canvasHelper.width = this.width;
            canvasHelper.height = this.width;

            canvasHelperCtx.clearRect(0, 0, this.width, this.width);
            canvasHelperCtx.beginPath();

            if (this.align == 'left') {
                canvasHelperCtx.moveTo(this.lineWidth / 2, this.width - this.lineWidth);
                canvasHelperCtx.lineTo(this.width, this.width - this.lineWidth);
                canvasHelperCtx.lineTo(this.lineWidth, this.lineWidth);
                canvasHelperCtx.lineTo(this.lineWidth, this.width - this.lineWidth);
            }

            if (this.align == 'right') {
                canvasHelperCtx.moveTo(this.lineWidth / 2, this.width - this.lineWidth);
                canvasHelperCtx.lineTo(this.width - this.lineWidth, this.width - this.lineWidth);
                canvasHelperCtx.lineTo(this.width - this.lineWidth, this.lineWidth);
                canvasHelperCtx.lineTo(this.lineWidth, this.width - this.lineWidth);
            }

            if (this.selected) {

                // start draw addition inner figure

                canvasHelperCtx.fillStyle = 'rgba(255,255,255, 1)';
                canvasHelperCtx.fill();

                canvasHelperCtx.strokeStyle = 'rgba(0, 0, 0, 1)';
                canvasHelperCtx.stroke();
                canvasHelperCtx.closePath();
                canvasHelperCtx.beginPath();

                canvasHelperCtx.lineWidth = this.lineWidth;

                if (this.align == 'left') {
                    canvasHelperCtx.moveTo(this.selectSize, this.width - this.selectSize);
                    canvasHelperCtx.lineTo(this.width - this.selectSize * 2, this.width - this.selectSize);
                    canvasHelperCtx.lineTo(this.selectSize, this.selectSize * 2);
                    canvasHelperCtx.lineTo(this.selectSize, this.width - this.selectSize);
                }

                if (this.align == 'right') {

                    canvasHelperCtx.moveTo(this.selectSize * 2, this.width - this.selectSize);
                    canvasHelperCtx.lineTo(this.width - this.selectSize, this.width - this.selectSize);
                    canvasHelperCtx.lineTo(this.width - this.selectSize, this.selectSize * 2);
                    canvasHelperCtx.lineTo(this.selectSize * 2, this.width - this.selectSize);
                }
            }

            var rgb = hexToRgb(this.color);
            canvasHelperCtx.fillStyle = 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ', 1)';
            canvasHelperCtx.fill();
            canvasHelperCtx.strokeStyle = 'rgba(0, 0, 0, 1)';
            canvasHelperCtx.stroke();

            this.imageData = canvasHelperCtx.getImageData(0, 0, this.width, this.width);
            ctx.drawImage(canvasHelper, this.position.x + this.paddingX, this.position.y + this.paddingY);

        }

        var colorSaverKey = colorSavers.length;
        colorSavers[colorSaverKey] = colorSaver;
    }

    var wheel = new Object;
    wheel.width = 18;
    wheel.imageData = null; // rendered wheel image data
    wheel.innerRadius;
    wheel.startAngle = 0; // 150
    wheel.outerRadius;
    wheel.outerStrokeStyle = 'rgba(0,0,0,0.2)';
    wheel.innerStrokeStyle = 'rgba(0,0,0,0.2)';
    wheel.pos; // updates in updateSize() | center point; wheel cursor \ hsv quad \ hsv triangle positioned relative that point
    wheel.draw = function () {

        // put rendered data

        if (this.imageData) {
            ctx.putImageData(this.imageData, 0, 0);
        } else {
            var hAngle = this.startAngle;
            for (var angle = 0; angle <= 360; angle++) {

                var startAngle = toRadians(angle - 2);
                var endAngle = toRadians(angle);

                ctx.beginPath();
                ctx.moveTo(center, center);
                ctx.arc(center, center, this.outerRadius, startAngle, endAngle, false);
                ctx.closePath();

                var targetRgb = hsvToRgb(hAngle / 360, 1, 1);
                ctx.fillStyle = 'rgb(' + targetRgb.r + ', ' + targetRgb.g + ', ' + targetRgb.b + ')';
                //ctx.fillStyle = 'hsl('+hAngle+', 100%, 50%)';
                ctx.fill();

                hAngle++;
                if (hAngle >= 360)
                    hAngle = 0;
            }

            ctx.globalCompositeOperation = "destination-out"; // cut out color wheel inside by circle next
            ctx.beginPath();
            ctx.arc(center, center, this.innerRadius, 0, PI * 2);

            ctx.fill();

            ctx.globalCompositeOperation = "source-over";
            ctx.strokeStyle = this.innerStrokeStyle; // 'rgba(0,0,0,0.2)';
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.closePath();

            // wheel border
            ctx.beginPath();
            ctx.arc(center, center, this.outerRadius, 0, PI * 2);
            ctx.strokeStyle = this.outerStrokeStyle;
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.closePath();

            this.imageData = ctx.getImageData(0, 0, wheelBlockSize, wheelBlockSize);
        }

    };

    wheel.isDotIn = function (dot) {
        // is dot in circle
        if (Math.pow(this.pos.x - dot.x, 2) + Math.pow(this.pos.y - dot.y, 2) < Math.pow(this.outerRadius, 2)) {
            if (Math.pow(this.pos.x - dot.x, 2) + Math.pow(this.pos.y - dot.y, 2) > Math.pow(this.innerRadius, 2)) {
                return true;
            }
        }
        return false;
    };

    var wheelCursor = new Object;
    wheelCursor.lineWeight = 2;
    wheelCursor.height = 4;
    wheelCursor.paddingX = 2; // padding from sides of wheel
    wheelCursor.path; // rotatePath2 --- поворот по старой функции, в фигуре не приплюсован центр

    var alphaSlider = new Object;
    alphaSlider.width = 18;
    alphaSlider.padding = 4;
    alphaSlider.outerStrokeStyle = 'rgba(0,0,0,0.2)';
    alphaSlider.innerStrokeStyle = 'rgba(0,0,0,0.2)';
    alphaSlider.height;
    alphaSlider.pos; // left top corner position
    alphaSlider.updateSize = function () {
        this.pos = {x: wheelBlockSize + alphaSlider.padding, y: alphaSlider.padding};
        this.height = wheelBlockSize - alphaSlider.padding * 2;
    };

    alphaSlider.draw = function () {
        var alphaGrd = ctx.createLinearGradient(0, 0, 0, this.height);
                
        var aRgb = hsvToRgb(hsv.h, 1, 1);
        
        alphaGrd.addColorStop(0, 'rgba(' + aRgb.r + ',' + aRgb.g + ',' + aRgb.b + ',1)');
        alphaGrd.addColorStop(1, 'rgba(' + aRgb.r + ',' + aRgb.g + ',' + aRgb.b + ',0)');

        ctx.beginPath();
        ctx.rect(this.pos.x, this.pos.y, this.width, this.height);
        ctx.fillStyle = "white";
        ctx.fill();
        ctx.fillStyle = alphaGrd;
        ctx.fill();

        ctx.strokeStyle = 'rgba(0,0,0, 0.2)';
        ctx.lineWidth = 2;

        ctx.stroke();
        ctx.closePath();
    };

    alphaSlider.dotToAlpha = function (dot) {
        return 1 - Math.abs(this.pos.y - dot.y) / this.height;
    };

    alphaSlider.alphaToDot = function (alpha) {
        return {
            x: 0,
            y: this.height - (this.height * alpha)
        };
    };

    alphaSlider.limitDotPosition = function (dot) {
        var y = dot.y;

        if (y < this.pos.y) {
            y = this.pos.y;
        }

        if (y > this.pos.y + this.height) {
            y = this.pos.y + this.height;
        }

        return {x: this.pos.x, y: y};
    };

    alphaSlider.isDotIn = function (dot) {
        if (dot.x < this.pos.x ||
                dot.x > this.pos.x + alphaSlider.width ||
                dot.y < this.pos.y ||
                dot.y > this.pos.y + this.height) {
            return false;
        }
        return true;
    };

    // svCursorMouse - для устройств с мышкой, генератор указателя в зависимости от активной области
    // todo on very very small sv when set by hex, cursor may be go out of bounds
    var svCursorMouse = new Object;

    svCursorMouse.svCursorData = null;
    svCursorMouse.stCursor = null; // cursor before replace
    svCursorMouse.curType = 0; // if > 0 cursor switched by KellyColorPicker to custom
    svCursorMouse.size = 16;
    svCursorMouse.cEl = document.body;

    svCursorMouse.initSvCursor = function () {
        if (!canvas)
            return false;

        this.curType = 1;

        if (!this.stCursor) {
            
            this.stCursor = window.getComputedStyle(this.cEl).cursor;            
                
            if (!this.stCursor) {
                this.stCursor = 'auto';
            }
        }        

        if (this.svCursorData) {
            this.cEl.style.cursor = this.svCursorData;
            return true;
        }

        if (!canvasHelper)
            return false;

        // create canvas on 2 pixels bigger for Opera that cut image 
        var canvasSize = this.size + 2;

        canvasHelper.width = canvasSize;
        canvasHelper.height = canvasSize;

        canvasHelperCtx.clearRect(0, 0, this.size, this.size);
        canvasHelperCtx.strokeStyle = 'rgba(255, 255, 255, 1)';

        canvasHelperCtx.beginPath();
        canvasHelperCtx.lineWidth = 2;
        canvasHelperCtx.arc(canvasSize / 2, canvasSize / 2, this.size / 2, 0, PI * 2);

        canvasHelperCtx.stroke();
        canvasHelperCtx.closePath();

        var offset = canvasSize; //if (input.value.indexOf(curImageData) !== -1)
        var curImageData = canvasHelper.toDataURL();

        this.svCursorData = 'url(' + curImageData + ') ' + offset / 2 + ' ' + offset / 2 + ', auto';

        if (!this.svCursorData)
            return false;

        this.cEl.style.cursor = this.svCursorData;
        if (this.cEl.style.cursor.indexOf(curImageData) === -1) { // for autist IE (Edge also), that not support data-uri for cursor -_-
            this.svCursorData = 'crosshair';
            this.cEl.style.cursor = 'crosshair';
        }
        return true;
    };

    svCursorMouse.initStandartCursor = function () {
        if (!this.stCursor)
            return;
        
        svCursorMouse.curType = 0;
        this.cEl.style.cursor = this.stCursor;
    };

    svCursorMouse.updateCursor = function (newDot) {
        if (!changeCursor)
            return;

        if (KellyColorPicker.cursorLock)
            return;

        if (svFig.isDotIn(newDot)) {
            svCursorMouse.initSvCursor();
        } else {
            svCursorMouse.initStandartCursor();
        }
    };

    // updateinput

    function constructor(cfg) {
        var criticalError = '', placeName = '';

        // save non-camelased old style options compatibility

        if (cfg.alpha_slider !== undefined) {
            cfg.alphaSlider = cfg.alpha_slider;
        }

        if (cfg.input_color !== undefined) {
            cfg.inputColor = cfg.input_color;
        }

        if (cfg.input_format !== undefined) {
            cfg.inputFormat = cfg.input_format;
        }

        // config apply

        if (cfg.input && typeof cfg.input !== 'object') {
            cfg.input = document.getElementById(cfg.input);
            input = cfg.input;
            // if (!cfg.input) log += '| "input" (' + inputName + ') not not found';
        } else if (typeof cfg.input === 'object') {
            input = cfg.input;
        }

        if (cfg.changeCursor !== undefined) {
            changeCursor = cfg.changeCursor;
        }

        if (cfg.alpha !== undefined) {
            a = cfg.alpha;
        }

        if (cfg.alphaSlider !== undefined) {
            alpha = cfg.alphaSlider;
        }

        if (cfg.inputColor !== undefined) {
            inputColor = cfg.inputColor;
        }

        if (cfg.inputFormat !== undefined) {
            inputFormat = cfg.inputFormat;
        }

        if (cfg.userEvents)
            userEvents = cfg.userEvents;

        if (cfg.place && typeof cfg.place !== 'object') {
            placeName = cfg.place;
            cfg.place = document.getElementById(cfg.place);
        }

        if (cfg.place) {
            place = cfg.place;
        } else if (input) {

            popup.tag = document.createElement('div');
            popup.tag.className = "popup-kelly-color";

            if (!cfg.popupClass) {

                popup.tag.className = "popup-kelly-color";

                popup.tag.style.position = 'absolute';
                popup.tag.style.bottom = '0px';
                popup.tag.style.left = '0px';
                popup.tag.style.display = 'none';
                popup.tag.style.backgroundColor = '#e1e1e1';
                popup.tag.style.border = "1px solid #bfbfbf";
                popup.tag.style.boxShadow = "7px 7px 14px -3px rgba(0,0,0,0.24)";
                popup.tag.style.borderTopLeftRadius = '4px';
                popup.tag.style.borderTopRightRadius = '4px';
                popup.tag.style.borderBottomLeftRadius = '4px';
                popup.tag.style.borderBottomRightRadius = '4px';
                popup.tag.style.padding = "12px";
                popup.tag.style.boxSizing = "content-box";

            } else {
                popup.tag.className = cfg.popupClass;
            }

            place = popup.tag;

            var body = document.getElementsByTagName('body')[0];
            body.appendChild(popup.tag);

            addEventListner(input, "click", function (e) {
                return handler.popUpShow(e);
            }, 'popup_');

        } // attach directly to input by popup
        else
            criticalError += '| "place" (' + placeName + ') not not found';

        // hex default #000000
        var colorData = false;

        if (cfg.color) {
            colorData = readColorData(cfg.color);
        } else if (input && input.value) {
            colorData = readColorData(input.value);
        }

        if (colorData) {
            hex = colorData.h;
            if (alpha)
                a = colorData.a;
        }

        //if (hex.charAt(0) == '#') hex = hex.slice(1);
        //if (hex.length == 3) hex = hex + hex;
        //if (hex.length !== 6) hex = '#000000';

        if (cfg.method && (cfg.method == 'triangle' || cfg.method == 'quad'))
            method = cfg.method;

        if (!initCanvas()) {
            criticalError += ' | cant init canvas context';
        }
        
        // size of elments init 
        
        if (cfg.resizeWith) {

            if (typeof cfg.resizeWith !== 'object' && typeof cfg.resizeWith !== 'boolean')
                cfg.resizeWith = document.getElementById(cfg.resizeWith);
            
            if (cfg.resizeWith === true) {
                resizeWith = canvas;
            } else {
                resizeWith = cfg.resizeWith;
            }
            
            if (cfg.resizeSide)
                resizeSide = cfg.resizeSide;                
                
            if (resizeWith) {
                var newSize = getSizeByElement(resizeWith);
                if (newSize)
                    cfg.size = getSizeByElement(resizeWith);
                
                addEventListner(window, "resize", function (e) {
                    return handler.syncSize(e);
                }, 'canvas_');
            }
        }
                
        if (cfg.size && cfg.size > 0) {
            wheelBlockSize = cfg.size;
        }
        
        // size init end
        
        if (criticalError) {
            if (typeof console !== 'undefined')
                console.log('KellyColorPicker : ' + criticalError);
            return;
        }

        if (method == 'quad')
            svFig = getSvFigureQuad();
        if (method == 'triangle')
            svFig = getSvFigureTriangle();

        if (input) {
            var inputEdit = function (e) {
                var e = e || window.event;
                if (!e.target) {
                    e.target = e.srcElement;
                }
                handler.setColorByHex(e.target.value, true);
            };

            addEventListner(input, "click", inputEdit, 'input_edit_');
            addEventListner(input, "change", inputEdit, 'input_edit_');
            addEventListner(input, "keyup", inputEdit, 'input_edit_');
            addEventListner(input, "keypress", inputEdit, 'input_edit_');
        }

        if (cfg.colorSaver) {
            initColorSaver('left', true);
            initColorSaver('right');
        }

        if (cfg.methodSwitch) {
            initStyleSwitch();
        }

        enableEvents();

        updateSize();
        handler.setColorByHex(false); // update color info and first draw
    }

    // may be zero in some cases / check before applay

    function getSizeByElement(el) {

        var sizeInfo = el.getBoundingClientRect();
        var size = 0;
        var sizeReduse = 0;
        if (alpha) {
            sizeReduse = alphaSlider.width + alphaSlider.padding * 2;
        }
        
        if (el === canvas) {
                 if (sizeInfo.width <= sizeInfo.height)
                size = sizeInfo.height;
            else if (sizeInfo.height < sizeInfo.width)
                size = sizeInfo.width; 
        } else {
        
            if (resizeSide) {
                    if (resizeSide == 'height')
                    size = sizeInfo.height;
                else if (resizeSide == 'width')
                    size = sizeInfo.width;
            } else {
                     if (sizeInfo.width > sizeInfo.height)
                    size = sizeInfo.height;
                else if (sizeInfo.height >= sizeInfo.width)
                    size = sizeInfo.width;
            }
        }
        
        size = parseInt(size);
        
        if (alpha) {

            size -= sizeReduse;
        }

        if (size <= 0) {
            return false;
        }

        return size;
    }

    // Read color value from string cString in rgb \ rgba \ hex \ hsl \ hsla format 
    // return array {h : color in rgb hex format (string #000000), a : alpha (float value from 0 to 1) }
    // falseOnFail = false - return default array on fail {h : '#000000', a : 1} or return false on fail if true

    function readColorData(cString, falseOnFail) {
        var alpha = 1;
        var h = false;

        cString = cString.trim(cString);
        
        if (cString.indexOf("(") == -1) { // hex color
        
            if (cString.charAt(0) == '#')
                cString = cString.slice(1);
            
            cString = cString.substr(0, 8);
            
            if (cString.length >= 3) {
                
                if (cString.length > 6 && cString.length < 8) {
                    cString = cString.substr(0, 6); // bad alpha data
                }
                
                if (cString.length > 3 && cString.length < 6) {
                    cString = cString.substr(0, 3); // bad full format 
                }
                
                h = cString;
                
                // complite full format, by replicating the R, G, and B values 
                
                if (cString.length >= 3 && cString.length <= 4) {
                    
                    h = "";
                    
                    for (let i = 0; i < cString.length; i++) {
                        h += cString[i] + cString[i];
                    }
                }
                
                if (h.length == 8)
                    alpha = (parseInt(h, 16) & 255) / 255;
                
            }
            
        } else {
            
            vals = cString.split(",");
            
            if (vals.length >= 3) {
                
                switch (cString.substring(0, 3)) {
                    
                    case 'rgb':
                    
                        vals[0] = vals[0].replace("rgba(", "");
                        vals[0] = vals[0].replace("rgb(", "");

                        var rgb = {r: parseInt(vals[0]), g: parseInt(vals[1]), b: parseInt(vals[2])};

                        if (rgb.r <= 255 && rgb.g <= 255 && rgb.b <= 255) {
                            h = rgbToHex(rgb);
                        }
                        
                        break;
                        
                    case 'hsl':
                    
                        vals[0] = vals[0].replace("hsl(", "");
                        vals[0] = vals[0].replace("hsla(", "");
                        
                        let hue = parseFloat(vals[0]) / 360.0;
                        let s = parseFloat(vals[1]) / 100.0; //js will ignore % in the end
                        let l = parseFloat(vals[2]) / 100.0;
                        
                        if (hue >= 0 && s <= 1 && l <= 1) {
                            rgb = hsvToRgb(hue, s, l);
                            h = rgbToHex(rgb);
                        }
                        
                        break;
                }
                
                if (vals.length == 4) {
                    
                    alpha = parseFloat(vals[3]);
                    
                    if (!alpha || alpha < 0)
                        alpha = 0;
                    
                    if (alpha > 1) 
                        alpha = 1;                    
                }
            }
        }

        if (h === false && falseOnFail)
            return false;
        
        if (h === false)
            h = '000000';
   
        if (h.charAt(0) != '#') {
            h = h.substr(0, 6);
            h = '#' + h;
        } else {
            h = h.substr(0, 7); // for private purposes must contain only rgb part
        }
        
        return {h: h, a: alpha};
    }

    function getSvFigureQuad() {

        if (svFigsPool['quad'])
            return svFigsPool['quad'];

        var quad = new Object;
        quad.size;
        quad.padding = 2;
        quad.path; // крайние точки фигуры на координатной плоскости
        quad.imageData = null; // rendered quad image data
        // перезаписывается существующий, чтобы не вызывать утечек памяти, обнуляя прошлый
        // тк UInt8ClampedArray генерируемый createImageData стандартными способами не
        // во всех браузерах выгружается сразу

        quad.dotToSv = function (dot) {
            return {
                s: Math.abs(this.path[3].x - dot.x) / this.size,
                v: Math.abs(this.path[3].y - dot.y) / this.size
            };
        };

        quad.svToDot = function (sv) {
            var quadX = this.path[0].x;
            var quadY = this.path[0].y;

            var svError = 0.02;
            if (wheelBlockSize < 150) {
                svError = 0.07;
            } else if (wheelBlockSize < 100) {
                svError = 0.16;
            }

            for (var y = 0; y < this.size; y++) {
                for (var x = 0; x < this.size; x++) {
                    var dot = {x: x + quadX, y: y + quadY};
                    var targetSv = this.dotToSv(dot);
                    var es = Math.abs(targetSv.s - sv.s), ev = Math.abs(targetSv.v - sv.v);

                    if (es < svError && ev < svError) {
                        return dot;
                    }
                }
            }

            return {x: 0, y: 0};
        };

        quad.limitDotPosition = function (dot) {
            var x = dot.x;
            var y = dot.y;

            if (x < this.path[0].x) {
                x = this.path[0].x;
            }

            if (x > this.path[0].x + this.size) {
                x = this.path[0].x + this.size;
            }

            if (y < this.path[0].y) {
                y = this.path[0].y;
            }

            if (y > this.path[0].y + this.size) {
                y = this.path[0].y + this.size;
            }

            return {x: x, y: y};
        };

        quad.draw = function () {
            if (!this.imageData)
                this.imageData = ctx.createImageData(this.size, this.size);
            var i = 0;

            var quadX = this.path[0].x;
            var quadY = this.path[0].y;

            for (var y = 0; y < this.size; y++) {
                for (var x = 0; x < this.size; x++) {
                    var dot = {x: x + quadX, y: y + quadY};

                    var sv = this.dotToSv(dot);
                    var targetRgb = hsvToRgb(hsv.h, sv.s, sv.v);
                    this.imageData.data[i + 0] = targetRgb.r;
                    this.imageData.data[i + 1] = targetRgb.g;
                    this.imageData.data[i + 2] = targetRgb.b;
                    this.imageData.data[i + 3] = 255;
                    i += 4;
                }
            }

            ctx.putImageData(this.imageData, quadX, quadY);

            ctx.beginPath();
            ctx.strokeStyle = 'rgba(0,0,0, 0.2)';
            ctx.lineWidth = 2;
            for (var i = 0; i <= this.path.length - 1; ++i)
            {
                if (i == 0)
                    ctx.moveTo(this.path[i].x, this.path[i].y);
                else
                    ctx.lineTo(this.path[i].x, this.path[i].y);
            }

            ctx.stroke();

            ctx.closePath();
        };

        quad.updateSize = function () {
            var workD = (wheel.innerRadius * 2) - wheelCursor.paddingX * 2 - this.padding * 2;

            // исходя из формулы диагонали квадрата, узнаем длинну стороны на основании доступного диаметра
            this.size = Math.floor(workD / Math.sqrt(2));

            this.path = new Array();

            // находим верхнюю левую точку и от нее задаем остальные координаты
            this.path[0] = {x: -1 * (this.size / 2), y: -1 * (this.size / 2)};
            this.path[1] = {x: this.path[0].x + this.size, y: this.path[0].y};
            this.path[2] = {x: this.path[1].x, y: this.path[1].y + this.size};
            this.path[3] = {x: this.path[2].x - this.size, y: this.path[2].y};
            this.path[4] = {x: this.path[0].x, y: this.path[0].y};

            for (var i = 0; i <= this.path.length - 1; ++i) {
                this.path[i].x += wheel.pos.x;
                this.path[i].y += wheel.pos.y;
            }
        }

        quad.isDotIn = function (dot) {
            if (dot.x < this.path[0].x ||
                    dot.x > this.path[0].x + this.size ||
                    dot.y < this.path[0].y ||
                    dot.y > this.path[0].y + this.size) {
                return false;
            }
            return true;
        };

        svFigsPool['quad'] = quad;
        return quad;
    }

    function getSvFigureTriangle() {

        if (svFigsPool['triangle'])
            return svFigsPool['triangle'];

        var triangle = new Object;
        triangle.size; // сторона равностороннего треугольника
        triangle.padding = 2;
        triangle.path;
        triangle.imageData = null; // rendered triangle image data
        triangle.followWheel = true;
        triangle.s;
        triangle.sOnTop = false;
        triangle.outerRadius;

        triangle.limitDotPosition = function (dot) {
            var x = dot.x;
            var y = dot.y;

            var slopeToCtr;
            var maxX = this.path[0].x;
            var minX = this.path[2].x;
            var finalX = x;
            var finalY = y;

            finalX = Math.min(Math.max(minX, finalX), maxX);
            var slope = ((this.path[0].y - this.path[1].y) / (this.path[0].x - this.path[1].x));
            var minY = Math.ceil((this.path[1].y + (slope * (finalX - this.path[1].x))));
            slope = ((this.path[0].y - this.path[2].y) / (this.path[0].x - this.path[2].x));
            var maxY = Math.floor((this.path[2].y + (slope * (finalX - this.path[2].x))));

            if (x < minX) {
                slopeToCtr = ((wheel.pos.y - y) / (wheel.pos.x - x));
                finalY = y;
            }

            finalY = Math.min(Math.max(minY, finalY), maxY);
            return {x: finalX, y: finalY};
        };

        triangle.svToDot = function (sv) {
            var svError = 0.02;
            if (wheelBlockSize < 150) {
                svError = 0.07;
            } else if (wheelBlockSize < 100) {
                svError = 0.16;
            }

            for (var y = 0; y < this.size; y++) {
                for (var x = 0; x < this.size; x++) {
                    var dot = {x: this.path[1].x + x, y: this.path[1].y + y};
                    if (svFig.isDotIn(dot)) {
                        var targetSv = this.dotToSv(dot);
                        var es = Math.abs(targetSv.s - sv.s), ev = Math.abs(targetSv.v - sv.v);

                        if (es < svError && ev < svError) {
                            return dot;
                        }
                    }
                }
            }

            return {
                x: 0,
                y: 0
            };
        };

        triangle.draw = function () {
            // no buffer

            if (!this.imageData)
                this.imageData = canvasHelperCtx.createImageData(this.size, this.size);

            canvasHelper.width = this.size;
            canvasHelper.height = this.size;

            var trX = this.path[1].x;
            var trY = this.path[1].y;
            var i = 0;
            for (var y = 0; y < this.size; y++) {
                for (var x = 0; x < this.size; x++) {
                    var dot = {x: this.path[1].x + x, y: this.path[1].y + y};
                    if (!svFig.isDotIn(dot)) {
                        this.imageData.data[i + 0] = 0;
                        this.imageData.data[i + 1] = 0;
                        this.imageData.data[i + 2] = 0;
                        this.imageData.data[i + 3] = 0;
                    } else {
                        var sv = this.dotToSv(dot);
                        var targetRgb = hsvToRgb(hsv.h, sv.s, sv.v);

                        this.imageData.data[i + 0] = targetRgb.r;
                        this.imageData.data[i + 1] = targetRgb.g;
                        this.imageData.data[i + 2] = targetRgb.b;
                        this.imageData.data[i + 3] = 255;
                    }

                    i += 4;
                }
            }

            canvasHelperCtx.putImageData(this.imageData, 0, 0);
            ctx.drawImage(canvasHelper, trX, trY); // draw with save overlaps transparent things , not direct putImageData that rewrite all pixels

            ctx.beginPath();
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)';
            ctx.lineWidth = 2;
            var trianglePath = this.path; //rotatePath(triangle.path, hsv.h * 360);
            for (var i = 0; i <= trianglePath.length - 1; ++i)
            {
                if (i == 0)
                    ctx.moveTo(trianglePath[i].x, trianglePath[i].y);
                else
                    ctx.lineTo(trianglePath[i].x, trianglePath[i].y);
            }

            ctx.stroke();
            ctx.closePath();
        };

        triangle.calcS = function (p) {
            return Math.abs((p[1].x - p[0].x) * (p[2].y - p[0].y) - (p[2].x - p[0].x) * (p[1].y - p[0].y)) / 2;
        };

        triangle.dotToSv = function (dot) {
            var p = getP({x: dot.x, y: dot.y}, this.vol);
            var len = getLen(p, this.vol[0]);

            // dirty tricks? replace output to interpolation and lerp in future
            if (len < 1)
                len = Math.floor(len);
            if (len > this.h - 1)
                len = this.h;

            var vol = len / (this.h);

            var angle = Math.abs(getAngle(dot, this.sSide));
            if (angle < 30)
                angle = 30;
            angle -= 30;
            angle = 60 - angle;
            angle = angle / 60; // - saturation from one angle

            return {s: angle, v: vol};
        };

        triangle.isDotIn = function (dot) {
            var t = [
                {x: this.path[0].x, y: this.path[0].y},
                {x: this.path[1].x, y: this.path[1].y},
                {x: dot.x, y: dot.y}
            ];

            var s = this.calcS(t);
            t[1] = {x: this.path[2].x, y: this.path[2].y};
            s += this.calcS(t);
            t[0] = {x: this.path[1].x, y: this.path[1].y};
            s += this.calcS(t);

            if (Math.ceil(s) == Math.ceil(this.s))
                return true;
            else
                return false;
        };

        triangle.updateSize = function () {
            // из формулы высоты равностороннего треугольника
            this.outerRadius = wheel.innerRadius - wheelCursor.paddingX - this.padding;
            // из теоремы синусов треугольника
            this.size = Math.floor((2 * this.outerRadius) * Math.sin(toRadians(60)));

            var h = ((Math.sqrt(3) / 2) * this.size);
            this.h = ((Math.sqrt(3) / 2) * this.size);

            this.path = new Array();
            this.path[0] = {x: this.outerRadius, y: 0}; // middle point - h
            this.path[1] = {x: this.path[0].x - h, y: -1 * (this.size / 2)}; // upper - s
            this.path[2] = {x: this.path[1].x, y: this.size / 2}; // bottom - v
            this.path[3] = {x: this.path[0].x, y: this.path[0].y}; // to begin

            for (var i = 0; i <= this.path.length - 1; ++i) {
                this.path[i].x += wheel.pos.x;
                this.path[i].y += wheel.pos.y;
            }

            this.vol = new Array();


            this.s = this.calcS(this.path);
            if (this.sOnTop) {
                var middle = getMiddlePoint(this.path[0], this.path[2]);

                this.vol[0] = {x: this.path[1].x, y: this.path[1].y};
                this.vol[1] = {x: middle.x, y: middle.y};

                this.sSide = this.path[1];
            } else {
                var middle = getMiddlePoint(this.path[0], this.path[1]);

                this.vol[0] = {x: this.path[2].x, y: this.path[2].y};
                this.vol[1] = {x: middle.x, y: middle.y};

                this.sSide = this.path[2];
            }
        };

        svFigsPool['triangle'] = triangle;
        return triangle;
    }

    // prefix - for multiple event functions for one object
    function addEventListner(object, event, callback, prefix) {
        if (typeof object !== 'object') {
            object = document.getElementById(object);
        }

        if (!object)
            return false;
        if (!prefix)
            prefix = '';

        events[prefix + event] = callback;

        if (!object.addEventListener) {
            object.attachEvent('on' + event, events[prefix + event]);
        } else {
            object.addEventListener(event, events[prefix + event]);
        }

        return true;
    }

    function removeEventListener(object, event, prefix) {
        if (typeof object !== 'object') {
            object = document.getElementById(object);
        }

        // console.log('remove :  : ' + Object.keys(events).length);
        if (!object)
            return false;
        if (!prefix)
            prefix = '';

        if (!events[prefix + event])
            return false;

        if (!object.removeEventListener) {
            object.detachEvent('on' + event, events[prefix + event]);
        } else {
            object.removeEventListener(event, events[prefix + event]);
        }

        events[prefix + event] = null;
        return true;
    }

    // [converters]
    // Read more about HSV color model :
    // https://ru.wikipedia.org/wiki/HSV_%28%F6%E2%E5%F2%EE%E2%E0%FF_%EC%EE%E4%E5%EB%FC%29
    // source of converter hsv functions
    // http://axonflux.com/handy-rgb-to-hsl-and-rgb-to-hsv-color-model-c

    function hsvToRgb(h, s, v) {
        var r, g, b, i, f, p, q, t;

        if (h && s === undefined && v === undefined) {
            s = h.s, v = h.v, h = h.h;
        }

        i = Math.floor(h * 6);
        f = h * 6 - i;
        p = v * (1 - s);
        q = v * (1 - f * s);
        t = v * (1 - (1 - f) * s);

        switch (i % 6) {
            case 0:
                r = v, g = t, b = p;
                break;
            case 1:
                r = q, g = v, b = p;
                break;
            case 2:
                r = p, g = v, b = t;
                break;
            case 3:
                r = p, g = q, b = v;
                break;
            case 4:
                r = t, g = p, b = v;
                break;
            case 5:
                r = v, g = p, b = q;
                break;
        }

        return {
            r: Math.floor(r * 255),
            g: Math.floor(g * 255),
            b: Math.floor(b * 255)
        };
    }

    function rgbToHsv(r, g, b) {
        if (r && g === undefined && b === undefined) {
            g = r.g, b = r.b, r = r.r;
        }

        r = r / 255, g = g / 255, b = b / 255;
        var max = Math.max(r, g, b), min = Math.min(r, g, b);
        var h, s, v = max;

        var d = max - min;
        s = max == 0 ? 0 : d / max;

        if (max == min) {
            h = 0; // achromatic
        } else {
            switch (max) {
                case r:
                    h = (g - b) / d + (g < b ? 6 : 0);
                    break;
                case g:
                    h = (b - r) / d + 2;
                    break;
                case b:
                    h = (r - g) / d + 4;
                    break;
            }
            h /= 6;
        }

        return {h: h, s: s, v: v};
    }

    function hexToRgb(hex) {
        var dec = parseInt(hex.charAt(0) == '#' ? hex.slice(1) : hex, 16);
        return {r: dec >> 16, g: dec >> 8 & 255, b: dec & 255};
    }

    function rgbToHex(color) {
        var componentToHex = function (c) {
            var hex = c.toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        };

        return "#" + componentToHex(color.r) + componentToHex(color.g) + componentToHex(color.b);
    }

    function toRadians(i) {
        return i * (PI / 180);
    }

    // [converters - end]

    function getLen(point1, point2) {
        return Math.sqrt(Math.pow(point1.x - point2.x, 2) + Math.pow(point1.y - point2.y, 2));
    }

    function getMiddlePoint(point1, point2) {
        return {x: (point1.x + point2.x) / 2, y: (point1.y + point2.y) / 2};
    }

    // перпендикуляр от точки

    function getP(point1, line1) {
        var l = (line1[0].x - line1[1].x) * (line1[0].x - line1[1].x) + (line1[0].y - line1[1].y) * (line1[0].y - line1[1].y);
        var pr = (point1.x - line1[0].x) * (line1[1].x - line1[0].x) + (point1.y - line1[0].y) * (line1[1].y - line1[0].y);
        var pt = true;
        var cf = pr / l;

        if (cf < 0) {
            cf = 0;
            pt = false;
        }
        if (cf > 1) {
            cf = 1;
            pt = false;
        }

        return {
            x: line1[0].x + cf * (line1[1].x - line1[0].x),
            y: line1[0].y + cf * (line1[1].y - line1[0].y),
            pt: pt
        };
    }

    // translate360 = true  270
    //            180 --- from.x.y --- 0
    //                      90

    function getAngle(point, from, translate360) {
        if (!from)
            from = {x: 0, y: 0};

        var distX = point.x - from.x;
        var distY = point.y - from.y;

        var a = Math.atan2(distY, distX) * 180 / (PI);
        if (translate360 && a < 0)
            a = 360 + a;

        return a;
    }

    // поворот фигуры относительно точки
    function rotatePath2(points, angle) {
        angle = toRadians(angle);
        var newPoints = new Array();

        for (var i = 0; i <= points.length - 1; ++i)
        {
            newPoints[i] = {
                x: points[i].x * Math.cos(angle) - points[i].y * Math.sin(angle),
                y: points[i].x * Math.sin(angle) + points[i].y * Math.cos(angle)
            };
        }

        return newPoints;
    }

    function updateSize() {
        padding = basePadding + wheelCursor.paddingX;

        rendered = false;
        wheel.imageData = null;

        center = wheelBlockSize / 2;
        wheel.pos = {x: center, y: center};

        wheel.outerRadius = center - padding;
        wheel.innerRadius = wheel.outerRadius - wheel.width;

        // объект относительно начала координат
        wheelCursor.path = [
            {x: wheel.innerRadius - wheelCursor.paddingX, y: wheelCursor.height * -1},
            {x: wheel.outerRadius + wheelCursor.paddingX, y: wheelCursor.height * -1},
            {x: wheel.outerRadius + wheelCursor.paddingX, y: wheelCursor.height},
            {x: wheel.innerRadius - wheelCursor.paddingX, y: wheelCursor.height},
            {x: wheel.innerRadius - wheelCursor.paddingX, y: wheelCursor.height * -1}
        ];

        var width = wheelBlockSize;
        if (alpha)
            width += alphaSlider.width + alphaSlider.padding * 2;

        if (place.tagName != 'CANVAS') {
            place.style.width = width + 'px';
            place.style.height = wheelBlockSize + 'px';
        }

        canvas.width = width;
        canvas.height = wheelBlockSize;
        
        if (resizeWith != canvas) {
            canvas.style.width = width + 'px';
            canvas.style.height = wheelBlockSize + 'px';
        }

        for (var i = 0; i <= colorSavers.length - 1; ++i)
        {
            colorSavers[i].updateSize();
        }

        if (styleSwitch) {

            styleSwitch.imageData['triangle'] = null;
            styleSwitch.imageData['quad'] = null;

            styleSwitch.updateSize();
        }

        svFig.updateSize();
        if (alpha)
            alphaSlider.updateSize();
    }

    // updates input after color changes (manualEnter = true if value entered from input, not from widget)
    // if manualEnter = true - save original text in input, else set input value in configurated format
    // if user event 'updateinput' is setted and return false - prevent default updateInput behavior

    function updateInput(manualEnter) {
        if (!input)
            return;

        if (userEvents["updateinput"]) {
            var callback = userEvents["updateinput"];
            if (!callback(handler, input, manualEnter))
                return;
        }
        
        let aStr = a.toFixed(2);
        let rgba = 'rgba(' + rgb.r + ', ' + rgb.g + ', ' + rgb.b + ', ' + aStr + ')';

        if (!manualEnter) {
            switch (inputFormat) {
                case 'mixed':
                    if (a < 1)
                        input.value = rgba;
                    else
                        input.value = hex;
                    break;
                case 'hex':
                    input.value = hex;
                    break;
                case 'hsla':
                    input.value = 'hsla(' + (hsv.h * 360).toFixed(2) + ', ' + (hsv.s * 100).toFixed(2) + '%, ' + (hsv.v * 100).toFixed(2) + '%, ' + aStr + ')';
                    break;
                default:
                    input.value = rgba;
                    break;
            }
        }

        if (inputColor) {
            if (hsv.v < 0.5) {
                input.style.color = "#FFF";
            } else {
                input.style.color = "#000";
            }

            input.style.background = rgba;
        }
    }

    function initCanvas() {
        if (!place)
            return false;
        if (place.tagName != 'CANVAS') {
            canvas = document.createElement('CANVAS');
            place.appendChild(canvas);
        } else {
            canvas = place;
        }

        // code for IE browsers
        if (typeof window.G_vmlCanvasManager != 'undefined') {
            canvas = window.G_vmlCanvasManager.initElement(canvas);
            canvasHelper = window.G_vmlCanvasManager.initElement(canvasHelper);
        }

        if (!!(canvas.getContext && canvas.getContext('2d'))) {
            ctx = canvas.getContext("2d");
            canvasHelperCtx = canvasHelper.getContext("2d");
            return true;
        } else
            return false;
    }

    // temp events until wait mouse click or touch
    function enableEvents() {
        addEventListner(canvas, "mousedown", function (e) {
            handler.mouseDownEvent(e);
        }, 'wait_action_');
        addEventListner(canvas, "touchstart", function (e) {
            handler.mouseDownEvent(e);
        }, 'wait_action_');
        addEventListner(canvas, "mouseout", function (e) {
            handler.mouseOutEvent(e);
        }, 'wait_action_');
        addEventListner(window, "touchmove", function (e) {
            handler.touchMoveEvent(e);
        }, 'wait_action_');
        addEventListner(canvas, "mousemove", function (e) {
            handler.mouseMoveRest(e);
        }, 'wait_action_');
    }

    // mouse detect canvas events

    function disableEvents() {
        removeEventListener(canvas, "mousedown", 'wait_action_');
        removeEventListener(canvas, "touchstart", 'wait_action_');
        removeEventListener(canvas, "mouseout", 'wait_action_');
        removeEventListener(window, "touchmove", 'wait_action_');
        removeEventListener(canvas, "mousemove", 'wait_action_');
    }

    function getEventDot(e) {
            
        e = e || window.event;
        var x, y;
        var scrollX = document.body.scrollLeft + document.documentElement.scrollLeft;
        var scrollY = document.body.scrollTop + document.documentElement.scrollTop;

        if (e.type == 'touchend') {
        
            x = e.changedTouches[0].clientX + scrollX;
            y = e.changedTouches[0].clientY + scrollY;
            
        } else if (e.type == 'touchmove' || e.touches) {
        
            x = e.touches[0].clientX + scrollX;
            y = e.touches[0].clientY + scrollY;
            
        } else {
            // e.pageX e.pageY e.x e.y bad for cross-browser
            x = e.clientX + scrollX;
            y = e.clientY + scrollY;
        }

        // set point to local coordinates
        
        var rect = canvas.getBoundingClientRect();
        x -= rect.left + scrollX;
        y -= rect.top + scrollY;

        return {x: x, y: y};
    }

    function selectColorSaver(key) {

        // disable current selection
        var previouseSelect = false;
        for (var i = 0; i <= colorSavers.length - 1; ++i)
        {
            if (colorSavers[i].selected)
                previouseSelect = i;
            colorSavers[i].selected = false;
        }

        // select new 
        var select = false;
        for (var i = 0; i <= colorSavers.length - 1; ++i)
        {
            if (i == key) {
                colorSavers[i].selected = true;
                handler.setColorByHex(colorSavers[i].color);
                select = true;
                break;
            }
        }

        if (select && userEvents["selectcolorsaver"]) {
            var callback = userEvents["selectcolorsaver"];
            callback(handler, colorSavers[key]);
        }

        if (!select && previouseSelect !== false) {
            colorSavers[previouseSelect].selected = true;
        }

        return select;
    }

    function updateColorSavers() {

        for (var i = 0; i <= colorSavers.length - 1; ++i)
        {
            if (colorSavers[i].selected)
                colorSavers[i].color = hex;
        }

    }

    function drawColorSavers() {
        if (colorSavers.length) {
            for (var i = 0; i <= colorSavers.length - 1; ++i)
            {
                colorSavers[i].draw();
            }
        }
    }

    // вывод интерфейса без курсоров
    // поддерживается буферизация todo добавить буферизацию color saver элементов
    // вынести буфер альфа слайдера отдельно от колеса и sv блока

    function drawColorPicker() {
        if (!ctx)
            return false;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // put buffered data
        if (rendered) {
            ctx.putImageData(canvasHelperData, 0, 0);
            drawColorSavers();
            return true;
        }

        // форма кольца может измениться только при изменении размеров виджета
        wheel.draw();
        svFig.draw();

        if (alpha)
            alphaSlider.draw();

        drawColorSavers();
        if (styleSwitch)
            styleSwitch.draw();

        // поместить текущее отрисованное изображение кольца + sv селектора в буфер
        // notice :
        // при перемещении курсора кольца сохранять буфер все изображение бессмысленно - sv блок постоянно обновляется, поэтому
        // сохраняем уже на событии выхода из процесса перемещения

        if (!drag) {
            //wheelBlockSize
            canvasHelperData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            rendered = true;
        }
        return true;
    }

    function draw() {
        if (!drawColorPicker()) {
            return false;
        }

        var curAngle = hsv.h * 360 - wheel.startAngle;

        // cursors

        if (alpha) {
            ctx.beginPath();
            var cursorHeight = 2;
            var cursorPaddingX = 2;
            var pointY = alphaSlider.height * (1 - a);
            ctx.rect(alphaSlider.pos.x - cursorPaddingX, alphaSlider.padding + pointY - cursorHeight / 2, alphaSlider.width + cursorPaddingX * 2, cursorHeight);
            ctx.strokeStyle = 'rgba(0,0,0, 0.8)';
            ctx.lineWidth = 2;

            ctx.stroke();
            ctx.closePath();
        }

        ctx.beginPath();

        var wheelCursorPath = rotatePath2(wheelCursor.path, curAngle, {x: wheel.pos.x, y: wheel.pos.y});
        for (var i = 0; i <= wheelCursorPath.length - 1; ++i)
        {
            wheelCursorPath[i].x += wheel.pos.x;
            wheelCursorPath[i].y += wheel.pos.y;
            if (i == 0)
                ctx.moveTo(wheelCursorPath[i].x, wheelCursorPath[i].y);
            else
                ctx.lineTo(wheelCursorPath[i].x, wheelCursorPath[i].y);
        }

        ctx.strokeStyle = 'rgba(0,0,0,0.8)';
        ctx.lineWidth = wheelCursor.lineWeight;
        ctx.stroke();
        ctx.closePath();

        // sv cursor
        if (hsv.v > 0.5 && hsv.s < 0.5)
            ctx.strokeStyle = 'rgba(0, 0, 0, 1)';
        else
            ctx.strokeStyle = 'rgba(255, 255, 255, 1)';
        //ctx.strokeStyle='rgba(255,255, 255, 1)';

        //document.getElementById('test3').value = 'h' + hsv.h.toFixed(2) + ' s'  + hsv.s.toFixed(2) + ' v'  + hsv.v.toFixed(2)

        ctx.beginPath();
        ctx.lineWidth = 2;
        ctx.arc(hsv.x, hsv.y, svCursor.radius, 0, PI * 2);


        ctx.stroke();
        ctx.closePath();

        return false;
    }

    this.popUpClose = function (e) {
        
        if (popup.tag === false)
            return;
       
        if (e) {
            // todo check when select color and then unpress button out of bounds
            if (e.target == input || e.target == canvas)
                return false;
            if (e.target == popup.tag)
                return false;
        }
 
        if (userEvents["popupclose"] && !userEvents["popupclose"](handler, e)) {
            return;
        }

        popup.tag.style.display = 'none';
        
        if (KellyColorPicker.activePopUp == handler)
            KellyColorPicker.activePopUp = false;
    }

    // if 'popupshow' user event is setted and return false - prevent show popup default behavior

    this.popUpShow = function (e) {
        if (popup.tag === false)
            return;

        if (userEvents["popupshow"] && !userEvents["popupshow"](handler, e)) {
            return;
        }

        // include once 
        if (!KellyColorPicker.popupEventsInclude) {
            addEventListner(document, "click", function (e) {
                if (KellyColorPicker.activePopUp)
                    return KellyColorPicker.activePopUp.popUpClose(e);
                else
                    return false;
            }, 'popup_close_');
            addEventListner(window, "resize", function (e) {
                if (KellyColorPicker.activePopUp)
                    return KellyColorPicker.activePopUp.popUpShow(e);
            }, 'popup_resize_');
            KellyColorPicker.popupEventsInclude = true;
        }

        if (KellyColorPicker.activePopUp) {
            KellyColorPicker.activePopUp.popUpClose(false);
        }

        var topMargin = handler.getCanvas().width;

        var alpha = handler.getAlphaFig();
        if (alpha) {
            topMargin -= alpha.width + alpha.padding;
        }
        
        var popupStyle = window.getComputedStyle(popup.tag);
        
        var paddingPopup = parseInt(popupStyle.paddingBottom) + parseInt(popupStyle.paddingTop);
        if (paddingPopup <= 0) {
            paddingPopup = 0;
        }

        var viewportOffset = input.getBoundingClientRect();
        var top = viewportOffset.top + (window.scrollY || window.pageYOffset || document.body.scrollTop) - paddingPopup;
        var left = viewportOffset.left + (window.scrollX || window.pageXOffset || document.body.scrollLeft);
        var padding = 6;

        popup.tag.style.top = (top - topMargin - popup.margin) + 'px';
        popup.tag.style.left = left + 'px';
        popup.tag.style.display = 'block';

        KellyColorPicker.activePopUp = handler;
        return false;
    }

    this.setHueByDot = function (dot) {
        var angle = getAngle(dot, wheel.pos) + wheel.startAngle;
        if (angle < 0)
            angle = 360 + angle;

        hsv.h = angle / 360;

        rgb = hsvToRgb(hsv.h, hsv.s, hsv.v);
        hex = rgbToHex(rgb);

        updateColorSavers();

        if (userEvents["change"]) {
            var callback = userEvents["change"];
            callback(handler);
        }

        updateInput();

        rendered = false;
        draw();
    };

    this.setColorForColorSaver = function (cString, align) {
        var colorData = readColorData(cString, true);
        if (!colorData)
            return;

        var colorSaver = handler.getColorSaver(align);
        if (colorSaver.selected) {
            this.setColorByHex(cString, false);
        } else {
            colorSaver.color = colorData.h;
            draw();
        }

        return true;
    };
    
    this.setColor = function(inputColor, manualEnter) {
        
        // synonym, since setColorByHex already accept color in different formats, not only in hex
        
        handler.setColorByHex(inputColor, manualEnter);
        
    } 

    // update color with redraw canvas and update input hex value
    // now support rgba \ rgb string format input
    // and also hsla \ hsl

    this.setColorByHex = function (inputHex, manualEnter) {

        if (!manualEnter)
            manualEnter = false;
        var inputAlpha = a;

        if (inputHex !== false) {

            if (!inputHex || !inputHex.length)
                return;

            var colorData = readColorData(inputHex, true);
            if (!colorData)
                return;

            inputHex = colorData.h;
            if (alpha)
                inputAlpha = colorData.a;

        } else
            inputHex = hex;

        if (alpha && inputHex == hex && rendered && inputAlpha != a) {
            a = inputAlpha;

            draw(); // slider always redraws in current even if part of canvas buffered
            return;
        }

        if (hex && inputHex == hex && rendered)
            return;

        // set and redraw all

        a = inputAlpha;
        rgb = hexToRgb(inputHex);
        hex = inputHex;
        hsv = rgbToHsv(rgb);

        var dot = svFig.svToDot(hsv);
        hsv.x = dot.x;
        hsv.y = dot.y;

        rendered = false;
        updateColorSavers();
        draw();

        if (userEvents["change"]) {
            var callback = userEvents["change"];
            callback(handler);
        }

        updateInput(manualEnter);
    };

    this.setAlphaByDot = function (dot) {
        a = alphaSlider.dotToAlpha(dot);

        if (userEvents["change"]) {
            var callback = userEvents["change"];
            callback(handler);
        }

        updateInput();
        draw();
    };

    this.setAlpha = function (alpha) {
        a = alpha;
        updateInput();
        draw();
    };

    this.setColorByDot = function (dot) {
        var sv = svFig.dotToSv(dot);

        hsv.s = sv.s;
        hsv.v = sv.v;
        hsv.x = dot.x;
        hsv.y = dot.y;

        if (hsv.s > 1)
            hsv.s = 1;
        if (hsv.s < 0)
            hsv.s = 0;
        if (hsv.v > 1)
            hsv.v = 1;
        if (hsv.v < 0)
            hsv.v = 0;

        rgb = hsvToRgb(hsv.h, hsv.s, hsv.v);
        hex = rgbToHex(rgb);

        updateColorSavers();

        if (userEvents["change"]) {
            var callback = userEvents["change"];
            callback(handler);
        }

        updateInput();
        draw();
    };

    this.mouseOutEvent = function (e) {
        if (svCursorMouse.curType > 0 && !KellyColorPicker.cursorLock) {
            svCursorMouse.initStandartCursor();
        }
    };

    // перемещение указателя по canvas в режиме покоя
    this.mouseMoveRest = function (e) {
        if (drag)
            return;

        if (!cursorAnimReady) {
            return;
        }

        cursorAnimReady = false;
        var newDot = getEventDot(e);
        svCursorMouse.updateCursor(newDot);
        requestAnimationFrame(function () {
            cursorAnimReady = true;
        });

        if (userEvents["mousemoverest"]) {
            var callback = userEvents["mousemoverest"];
            callback(e, handler, newDot);
        }
    };

    // to prevent scroll by touches while change color
    // в FireFox под андройд есть "фича" которая скрывает или раскрывает тулбар адресной строки при движении пальцем
    // отключить её можно только через опцию about:config browser.chrome.dynamictoolbar

    this.touchMoveEvent = function (e) {
        if (drag) { // todo check number of touches to ignore zoom action
            event.preventDefault();
        }
    };

    // маршрутизатор событий нажатий на элементы
    this.mouseDownEvent = function (event) {
        event.preventDefault();

        var move, up = false;
        var newDot = getEventDot(event);
        // console.log('mouseDownEvent : cur : ' + newDot.x + ' | ' + newDot.y);

        if (wheel.isDotIn(newDot)) {
            drag = 'wheel';
            handler.setHueByDot(newDot);

            move = function (e) {
                handler.wheelMouseMove(e, newDot);
            };
            up = function (e) {
                KellyColorPicker.cursorLock = false;
                handler.wheelMouseUp(e, newDot);
            };

        } else if (svFig.isDotIn(newDot)) {
            drag = 'sv';
            handler.setColorByDot(newDot);

            move = function (e) {
                handler.svMouseMove(e, newDot);
            };
            up = function (e) {
                KellyColorPicker.cursorLock = false;
                handler.svMouseUp(e, newDot);
            };
        } else if (alpha && alphaSlider.isDotIn(newDot)) {
            drag = 'alpha';
            handler.setAlphaByDot(newDot);

            move = function (e) {
                handler.alphaMouseMove(e, newDot);
            };
            up = function (e) {
                KellyColorPicker.cursorLock = false;
                handler.alphaMouseUp(e, newDot);
            };
        } else if (styleSwitch && styleSwitch.isDotIn(newDot)) {
            handler.setMethod();
        } else if (colorSavers.length) { // here all items with post check of dot in

            for (var i = 0; i <= colorSavers.length - 1; ++i)
            {
                if (colorSavers[i].isDotIn(newDot)) {
                    selectColorSaver(i);
                    break;
                }
            }
        }

        if (move && up) {
            disableEvents();
            KellyColorPicker.cursorLock = handler;
            addEventListner(document, "mouseup", up, 'action_process_');
            addEventListner(document, "mousemove", move, 'action_process_');
            addEventListner(document, "touchend", up, 'action_process_');
            addEventListner(document, "touchmove", move, 'action_process_');
        }
    };

    this.wheelMouseMove = function (event, dot) {
        event.preventDefault();

        if (!drag)
            return;

        if (!cursorAnimReady) {
            return;
        }
        cursorAnimReady = false;
        var newDot = getEventDot(event);

        // console.log('wheelMouseMove : start : ' + dot.x + ' | ' + dot.y + ' cur : ' + newDot.x + ' | ' + newDot.y);
        requestAnimationFrame(function () {
            cursorAnimReady = true;
        });
        //setTimeout(function() {cursorAnimReady = true;}, 1000/30);

        handler.setHueByDot(newDot);

        if (userEvents["mousemoveh"]) {
            var callback = userEvents["mousemoveh"];
            callback(event, handler, newDot);
        }
    };

    this.wheelMouseUp = function (event, dot) {
        event.preventDefault();
        if (!drag)
            return;
        //console.log('wheelMouseUp : start : ' + dot.x + ' | ' + dot.y);

        removeEventListener(document, "mouseup", 'action_process_');
        removeEventListener(document, "mousemove", 'action_process_');
        removeEventListener(document, "touchend", 'action_process_');
        removeEventListener(document, "touchmove", 'action_process_');

        enableEvents();
        drag = false;

        rendered = false;
        draw();

        var newDot = getEventDot(event);
        svCursorMouse.updateCursor(newDot);

        if (userEvents["mouseuph"]) {
            var callback = userEvents["mouseuph"];
            callback(event, handler, newDot);
        }
    };

    this.alphaMouseMove = function (event, dot) {
        event.preventDefault();
        if (!drag)
            return;

        if (!cursorAnimReady) {
            return;
        }

        cursorAnimReady = false;
        var newDot = getEventDot(event);

        // console.log('svMouseMove : start : ' + dot.x + ' | ' + dot.y + ' cur : ' + newDot.x + ' | ' + newDot.y);

        newDot = alphaSlider.limitDotPosition(newDot);

        requestAnimationFrame(function () {
            cursorAnimReady = true;
        });
        //setTimeout(function() {cursorAnimReady = true;}, 1000/30);

        handler.setAlphaByDot(newDot);

        if (userEvents["mousemovealpha"]) {
            var callback = userEvents["mousemovealpha"];
            callback(event, handler, newDot);
        }
    };

    this.alphaMouseUp = function (event, dot) {
        event.preventDefault();
        if (!drag)
            return;

        removeEventListener(document, "mouseup", 'action_process_');
        removeEventListener(document, "mousemove", 'action_process_');
        removeEventListener(document, "touchend", 'action_process_');
        removeEventListener(document, "touchmove", 'action_process_');

        enableEvents();
        drag = false;

        var newDot = getEventDot(event);
        svCursorMouse.updateCursor(newDot);

        if (userEvents["mouseupalpha"]) {
            var callback = userEvents["mouseupalpha"];
            callback(event, handler, newDot);
        }
    };

    this.svMouseMove = function (event, dot) {
        event.preventDefault();
        if (!drag)
            return;

        if (!cursorAnimReady) {
            return;
        }

        cursorAnimReady = false;
        var newDot = getEventDot(event);

        // console.log('svMouseMove : start : ' + dot.x + ' | ' + dot.y + ' cur : ' + newDot.x + ' | ' + newDot.y);

        newDot = svFig.limitDotPosition(newDot);

        requestAnimationFrame(function () {
            cursorAnimReady = true;
        });
        //setTimeout(function() {cursorAnimReady = true;}, 1000/30);

        handler.setColorByDot(newDot);

        if (userEvents["mousemovesv"]) {
            var callback = userEvents["mousemovesv"];
            callback(event, handler, newDot);
        }
    };

    this.svMouseUp = function (event, dot) {
        event.preventDefault();
        if (!drag)
            return;

        // console.log('svMouseUp : start : ' + dot.x + ' | ' + dot.y);

        removeEventListener(document, "mouseup", 'action_process_');
        removeEventListener(document, "mousemove", 'action_process_');
        removeEventListener(document, "touchend", 'action_process_');
        removeEventListener(document, "touchmove", 'action_process_');

        enableEvents();
        drag = false;

        var newDot = getEventDot(event);
        svCursorMouse.updateCursor(newDot);
        
        // todo 
        // split cached data for sv + h wheel and slider, so we can redraw alpha slider without performanse lost in svMouseMove
        
        if (alpha) {
            rendered = false;
            draw();
        }
        
        if (userEvents["mouseupsv"]) {
            var callback = userEvents["mouseupsv"];
            callback(event, handler, newDot);
        }
    };

    this.addUserEvent = function (event, callback) {
        userEvents[event] = callback;
        return true;
    };

    this.removeUserEvent = function (event) {
        if (!userEvents[event])
            return false;
        userEvents[event] = null;
        return true;
    };

    // для кастомизации отображения элементов виджета

    this.getCanvas = function () {
        if (!ctx)
            return false;
        return canvas;
    };

    this.getCtx = function () {
        if (!ctx)
            return false;
        return ctx;
    };

    this.getInput = function () {
        return input;
    };
    
    this.getSvFig = function () {
        return svFig;
    };
    
    this.getSvFigCursor = function () {
        return svCursor;
    };

    this.getWheel = function () {
        return wheel;
    };
    
    this.getWheelCursor = function () {
        return wheelCursor;
    };

    this.getCurColorHsv = function () {
        return hsv;
    };
    
    this.getCurColorRgb = function () {
        return rgb;
    };
    
    this.getCurColorHex = function () {
        return hex;
    };
    
    this.getCurColorRgba = function () {
        return {r: rgb.r, g: rgb.g, b: rgb.b, a: a};
    };
    
    this.getCurAlpha = function () {
        return a;
    };
    
    this.getAlphaFig = function () {
        if (alpha)
            return alphaSlider;
        else
            return false;
    }

    this.getPopup = function () {
        return popup;
    };
    
    this.getSize = function () {
        return wheelBlockSize;
    };

    // if align not setted get selected
    this.getColorSaver = function (align) {
        for (var i = 0; i <= colorSavers.length - 1; ++i)
        {
            if ((!align && colorSavers[i].selected) || colorSavers[i].align == align) {
                colorSavers[i].rgb = hexToRgb(colorSavers[i].color);
                colorSavers[i].hsv = rgbToHsv(colorSavers[i].rgb.r, colorSavers[i].rgb.g, colorSavers[i].rgb.b);
                return colorSavers[i];
            }
        }
    };

    this.setColorSaver = function (align) {

        if (!align)
            return false;

        for (var i = 0; i <= colorSavers.length - 1; ++i)
        {
            if (colorSavers[i].align == align) {
                selectColorSaver(i);
                return colorSavers[i];
            }
        }
    }

    this.updateView = function (dropBuffer) {
        if (!ctx)
            return false;

        if (dropBuffer) {
            wheel.imageData = null;
            svFig.imageData = null;
            canvasHelperData = null;
        }

        rendered = false;
        updateSize();
        draw();
        return true;
    };

    // resize canvas, with all data \ full refresh view
    // if size same as current and refresh variable setted to true - refresh current view anyway
    // othervise exit with return true

    this.resize = function (size, refresh) {
        if (!ctx)
            return false;
        if (size == wheelBlockSize && !refresh)
            return true;

        rendered = false;
        wheel.imageData = null;
        svFig.imageData = null;
        canvasHelperData = null;
        wheelBlockSize = size;
        updateSize();

        handler.setColorByHex(false);
        return false;
    };

    this.syncSize = function (e) {

        if (!resizeWith)
            return false;

        var newSize = getSizeByElement(resizeWith);
        if (newSize)
            handler.resize(newSize);
        return false;
    }

    this.setMethod = function (newMethod) {
        if (!newMethod) {
            newMethod = 'triangle';
            if (method == 'triangle')
                newMethod = 'quad';
        }

        if (newMethod == method)
            return false;
        if (method != 'quad' && method != 'triangle')
            return false;

        method = newMethod;

        if (method == 'quad')
            svFig = getSvFigureQuad();
        if (method == 'triangle')
            svFig = getSvFigureTriangle();

        handler.resize(wheelBlockSize, true);

        if (userEvents["setmethod"]) {
            var callback = userEvents["setmethod"];
            callback(handler, method);
        }

        return true;
    }

    // restore color of input ? 

    this.destroy = function () {
        if (!handler) {
            return false;
        }

        if (svCursorMouse.curType > 0) {
            KellyColorPicker.cursorLock = false;
            svCursorMouse.initStandartCursor();
        }

        if (drag) {
            removeEventListener(document, "mouseup", 'action_process_');
            removeEventListener(document, "mousemove", 'action_process_');
            removeEventListener(document, "touchend", 'action_process_');
            removeEventListener(document, "touchmove", 'action_process_');

            drag = false;
        }

        if (popup.tag) {
            removeEventListener(input, "click", "popup_");
        }

        if (input) {
            removeEventListener(input, "click", 'input_edit_');
            removeEventListener(input, "change", 'input_edit_');
            removeEventListener(input, "keyup", 'input_edit_');
            removeEventListener(input, "keypress", 'input_edit_');
        }

        // remove popup close and resize events if this picker include them erlier
        if (KellyColorPicker.popupEventsInclude && events['popup_close_click']) {
            if (KellyColorPicker.activePopUp)
                KellyColorPicker.activePopUp.popUpClose(false);

            removeEventListener(document, "click", 'popup_close_');
            removeEventListener(window, "resize", 'popup_resize_');

            KellyColorPicker.popupEventsInclude = false;
        }

        wheel.imageData = null;
        svFig.imageData = null;
        canvasHelperData = null;
        canvasHelper = null;

        if (place && place.parentNode) {
            place.parentNode.removeChild(place);
        }

        if (resizeWith) {
            removeEventListener(window, "resize", 'canvas_');
        }

        disableEvents(); // remove canvas events		

        // debug test for check is all events removed 
        // for (var key in events) {
        // 	console.log('key : ' +  key + ' data ' + events[key]);
        // }

        handler = null;
    };

    constructor(cfg);
}

/* static methods */

/**
 * Тригер для объектов KellyColorPicker, чтобы не сбрасывали стиль курсора при наведении если уже идет выбор цвета
 * Notice : при выходе курсора за границы текущего canvas, событие неизвестного объекта всегда может сбросить изображение курсора
 */

KellyColorPicker.cursorLock = false; // можно указывать handler объекта
KellyColorPicker.activePopUp = false;
KellyColorPicker.popupEventsInclude = false; // include events for document and window once for all elements

KellyColorPicker.attachToInputByClass = function (className, cfg) {

    var colorPickers = new Array();
    var inputs = document.getElementsByClassName(className);


    for (var i = 0; i < inputs.length; i++) {

        if (cfg)
            cfg.input = inputs[i];
        else
            cfg = {input: inputs[i], size: 150};

        colorPickers.push(new KellyColorPicker(cfg));
    }

    return colorPickers;
};

// KellyColorPicker.dragTrigger = false;
