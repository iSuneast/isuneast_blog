// import utils
document.write('<script src="./static/utils.js"></script>');

function GameConf() {
  this.balls = null;
  this.numBalls = null;
  // timer
  this.startTime = null;
  this.clearTime = null;
  this.timerStyle = null;
  // button
  this.startButtonBalls = null;
  // conf
  this.color = null;
  this.gameMode = null;
  // data
  this.text = null;
  this.fontsize = null;
  this.ballRadius = null;
  this.drawStartButton = function () {
    return this.gameMode == true && !this.started();
  }
  this.onClick = function (pos) {
    if (!this.started()) {
      if (this.startButtonBalls[0].isPointInside(pos.x, pos.y)) {
        for (var i = 0; i < this.balls.length; ++i) {
          if (this.balls[i].alive != 1) {
            return ;
          }
        }
        this.startGame();
      }
    }
  }
  this.init = function () {
    this.color = new RandomPickHashMap();
    this.color.add('blue', '#3A5BCD');
    this.color.add('red', '#EF2B36');
    this.color.add('yellow', '#FFC636');
    this.color.add('green', '#02A817');
  }
  this.initGame = function (canvas, text, fontsize, ballRadius, gameMode) {
    this.text = text;
    this.fontsize = fontsize;
    this.ballRadius = ballRadius;

    renderBalls(canvas, text, fontsize, ballRadius);
    this.startTime = null;
    this.clearTime = null;
    this.timerStyle = null;
    this.gameMode = gameMode;
    if (gameMode == true) {
      this.initStartButton(canvas);
    }
  }
  this.initStartButton = function (canvas) {
    var style = randomPickColor(this.color, 3);
    var x = canvas.width / 2.;
    var y = canvas.height / 2.;

    var outer = new Ball(x, y, 70, style[0], 0.6);
    var inner = new Ball(x, y, 50, style[1], 0.8);
    var tri1 = new Ball(x - 20, y - 30, 0, style[2], 0.9);
    var tri2 = new Ball(x + 37, y, 0, style[2], 0.9);
    var tri3 = new Ball(x - 20, y + 30, 0, style[2], 0.9);

    this.startButtonBalls = [outer, inner, tri1, tri2, tri3];
  }
  this.started = function () {
    return this.startTime != null;
  }

  this.escapedTime = function (curTime) {
    if (this.startTime == null) {
      return 0;
    } else {
      return curTime - this.startTime;
    }
  }
  this.startGame = function () {
    this.startTime = (new Date()).getTime();
    console.log('game started: ' + this.startTime);
  }
}

var gameConf = new GameConf();

function isEmptyPixel(data, row, col, width, height) {
  if (0 <= row && row < height && 0 <= col && col < width) {
    var offset = (row * width + col) * 4;
    for (var i = 0; i < 4; ++i) {
      if (data[offset + i] != 0) {
        return false;
      }
    }
  }
  return true;
}

function floodFill(data, width, height, row, col) {
  var dx = [0, 0, 1, -1, 1, 1, -1, -1];
  var dy = [1, -1, 0, 0, 1, -1, 1, -1]; 
  var pixels = new RandomPickHashSet();
  pixels.add([row, col]);
  for (var i = 0; i < pixels.vec.length; ++i) {
    cur = pixels.vec[i];
    for (var d = 0; d < dx.length; ++d) {
      var tx = cur[0] + dx[d];
      var ty = cur[1] + dy[d];
      if (!pixels.find([tx, ty]) && !isEmptyPixel(data, tx, ty, width, height)) {
        pixels.add([tx, ty]);
      }
    }
  }
  return pixels.vec;
}

function findPixels(data, width, height) {
  var pixels = new RandomPickHashMap();
  var numCC = 0;
  for (var col = 0; col < width; ++col) {
    for (var row = 0; row < height; ++row) {
      if (!isEmptyPixel(data, row, col, width, height) 
        && !pixels.find([col, row])) {
        var cc = floodFill(data, width, height, row, col);
        for (var i = 0; i < cc.length; ++i) {
          pixels.add([cc[i][1], cc[i][0]], numCC);
        }
        ++numCC;
      }
    }
  }
  return {
    pixels: pixels,
    numCC: numCC
  };
}

function drawText(canvas, text, fontsize, alpha) {
  if (alpha == null) {
    alpha = 1;
  }
  var context = canvas.getContext('2d');
  context.font = fontsize + 'px Lato';
  context.textAlign = 'center';
  context.globalAlpha = alpha;
  context.fillText(text, canvas.width/2, canvas.height/1.5);  
}

function renderBalls(canvas, text, fontsize, ballRadius) {
  canvas = canvas.cloneNode();
  var width = canvas.width;
  var height = canvas.height;
  var context = canvas.getContext('2d');
  context.clearRect(0, 0, width, height);
  drawText(canvas, text, fontsize);
  var data = context.getImageData(0, 0, width, height).data;
  var newBalls = findBalls(data, width, height, ballRadius);
  gameConf.numBalls = newBalls.length;
  gameConf.balls = matchNewsBalls(gameConf.balls, newBalls);
}

function randomPickColor(colors, num, numTry) {
  if (numTry == null) {
    numTry = 7;
  }
  var bestColor = [];
  var bestScore = -1e9;
  for (; numTry > 0; --numTry) {
    var score = 0;
    var color = [];
    for (var i = 0; i < num; ++i) {
      var tmp;
      do {
        tmp = colors.pickVal();
      } while (i > 0 && tmp == color[i-1]);
      color.push(tmp);
      for (var j = 0; j < i; ++j) {
        if (color[j] == color[i]) {
          score -= 1. / (i - j - 1);
        }
      }
    }
    if (score > bestScore) {
      bestScore = score;
      bestColor = color;
    }
  }
  return bestColor;
}

function findBalls(data, width, height, ballRadius) {
  var radius = new function () {
    this.min = ballRadius;
    this.max = ballRadius;
    this.pick = function() {
      return randomInt(this.min, this.max);
    }
  }

  var cc = findPixels(data, width, height);
  var pixels = cc.pixels;
  ccColor = randomPickColor(gameConf.color, cc.numCC);

  balls = [];
  for (var numBalls = 314; numBalls > 0; --numBalls) {
    if (pixels.size() <= 0) {
      break;
    }
    var p = pixels.pick();
    var r = radius.pick();
    var c = ccColor[pixels.get(p)];
    var ball = new Ball(p[0], p[1], r, c);
    balls.push(ball);
    quickRemove(pixels, p, r);
  }
  console.log('num balls: ' + balls.length);

  return balls;
}

function quickRemove(hm, p, r) {
  var lim = r * r;
  for (var x = -r; x <= r; ++x) {
    for (var y = -r; y <= r; ++y) {
      if (x * x + y * y <= lim) {
        hm.remove([p[0] + x, p[1] + y]);        
      }
    }
  }    
}

function getMousePos(canvas, evt) {
  var rect = canvas.getBoundingClientRect();
  return {
    x: evt.clientX - rect.left,
    y: evt.clientY - rect.top
  };
}

function updateBalls(canvas, balls, timeDiff, mousePos, moveForceMul) {
  // friction^2 > 4 restoreForce
  // timeDiff: around 20
  /*
  var friction = 0.005 * timeDiff;
  var moveForce = 10 * timeDiff;
  var restoreForce = 0.002 * timeDiff;
  */
  if (moveForceMul == null) {
    moveForceMul = 10;
  }
  var friction = 0.005 * timeDiff;
  var moveForce = moveForceMul * timeDiff;
  var restoreForce = 0.002 * timeDiff;

  for(var n = 0; n < balls.length; n++) {
    var ball = balls[n];
    ball.move();
    ball.restoreForces(restoreForce);
    ball.moveForces(mousePos.x, mousePos.y, moveForce);
    ball.friction(friction);
    ball.testCollision(canvas.width, canvas.height);
  }
}

function Ball(x, y, r, color, alpha) {
  if (alpha == null) {
    alpha = 1;
  }
  this.x = x;
  this.y = y;
  this.vx = 0;
  this.vy = 0;
  // 
  this.color = color;
  this.origX = x;
  this.origY = y;
  this.radius = r;
  //
  this.alpha = alpha;
  this.alive = 1;
  //
  this.isPointInside = function (x, y) {
    return this.sqrDist(x, y) <= this.radius * this.radius;
  }
  this.sqrDist = function (x, y) {
    var dx = this.x - x;
    var dy = this.y - y;
    return dx * dx + dy * dy;
  }
  this.draw = function (context) {
    context.beginPath();
    context.arc(this.x, this.y, this.radius, 0, 2 * Math.PI, false);
    context.fillStyle = this.color;
    context.globalAlpha = this.alpha;
    context.fill();
  }
  this.fadeout = function () {
    if (this.alive == 0) {
      this.radius *= 1.03;
      this.alpha *= 0.9;
      /*
       0.9 ^ k < 0.001
       k >= log (0.001) / log (0.9) > 3.14
       */
      if (this.alpha < 0.001) {
        this.alpha = 0;
        this.radius = 0;
        this.alive = -1;
      }
    }
  }
  this.move = function () {
    this.y += this.vy;
    this.x += this.vx;
  }
  this.demon = function (tar) {
    this.x = tar.x;
    this.y = tar.y;
    this.vx = tar.vx;
    this.vy = tar.vy;
  }
  this.outside = function (canvas) {
    return this.x < 0 || this.x >= canvas.width || this.y < 0 || this.y > canvas.height;
  }
  this.restoreForces = function (force) {
    this.vx -= force * (this.x - this.origX);
    this.vy -= force * (this.y - this.origY);
  }
  this.testCollision = function (width, height, collisionDamper) {
    if (gameConf.started()) {
      return ;
    }
    if (collisionDamper == null) {
      collisionDamper = 0.314;
    }
    var multiplier = - (1 - collisionDamper);
    // ceil
    if(this.y < this.radius) {
      this.y = this.radius + this.radius;
      this.vy *= multiplier;
    }
    // floor
    if(this.y > height - this.radius) {
      this.y = height - this.radius - this.radius;
      this.vy *= multiplier;
    }
    // left
    if(this.x < this.radius) {
      this.x = this.radius + this.radius;
      this.vx *= multiplier;
    }
    // right
    if(this.x > width - this.radius) {
      this.x = width - this.radius - this.radius;
      this.vx *= multiplier;
    }
  }
  this.moveForces = function (x, y, force) {
    var dx = this.x - x;
    var dy = this.y - y;

    var radius = Math.sqrt(Math.pow(dx, 2) + Math.pow(dy, 2));
    var totalDist = Math.abs(dx) + Math.abs(dy);
    var forceX = (Math.abs(dx) / totalDist) * (1 / radius) * force;
    var forceY = (Math.abs(dy) / totalDist) * (1 / radius) * force;

    this.vx += sign(dx) * forceX;
    this.vy += sign(dy) * forceY;
  }
  this.friction = function (force) {
    this.vx -= force * this.vx;
    this.vy -= force * this.vy;
  }
}

function orderBalls(balls) {
  var hm = {};
  for (var i = 0; i < balls.length; ++i) {
    var ball = balls[i];
    if (ball.alive != 1) {
      continue;
    }
    // every ball is dying
    ball.alive = 0;
    if (hm.hasOwnProperty(ball.color)) {
      hm[ball.color].push(ball);
    } else {
      hm[ball.color] = [ball];
    }
  }
  return hm;
}

function matchNewsBalls(oldBalls, newBalls) {
  if (oldBalls == null || oldBalls.length == 0) {
    return newBalls;
  }
  var hm = orderBalls(oldBalls);
  var balls = [];
  for (var i = 0; i < newBalls.length; ++i) {
    var ball = newBalls[i];
    if (hm.hasOwnProperty(ball.color)) {
      var cands = hm[ball.color];
      var oldBall = cands[randomInt(0, cands.length)];
      ++oldBall.alive;
      ball.demon(oldBall);
    } else {
      var oldBall = oldBalls[randomInt(0, oldBalls.length)];
      ball.demon(oldBall);      
    }
    balls.push(ball);
  }

  for (var i = 0; i < oldBalls.length; ++i) {
    var oldBall = oldBalls[i];
    if (oldBall.alive == 0) {
      balls.push(oldBall);
    }
  }

  return balls;
}
