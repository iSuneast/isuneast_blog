// import utils
document.write('<script src="/static/utils.js"></script>');

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
  console.log('num valid pixels: ' + pixels.size());
  console.log('num cc: ' + numCC);
  return {
    pixels: pixels,
    numCC: numCC
  };
}

function renderBalls(canvas, text, fontsize, ballRadius) {
  var context = canvas.getContext('2d');
  context.font = fontsize + 'px Lato';
  context.textAlign = 'center';
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillText(text, canvas.width/2, canvas.height/1.5);
  var data = context.getImageData(0, 0, canvas.width, canvas.height).data;

  return findBalls(data, canvas.width, canvas.height, ballRadius);
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
  console.log(bestColor);
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

  var color = new RandomPickHashMap();
  color.add('blue', '#3A5BCD');
  color.add('red', '#EF2B36');
  color.add('yellow', '#FFC636');
  color.add('green', '#02A817');

  var cc = findPixels(data, width, height);
  var pixels = cc.pixels;
  ccColor = randomPickColor(color, cc.numCC);

  balls = [];
  for (var numBalls = 314; numBalls > 0; --numBalls) {
    if (pixels.size() <= 0) {
      break;
    }
    var p = pixels.pick();
    var r = radius.pick();
    var c = ccColor[pixels.get(p)];
    var ball = new Ball(p[0], p[1], r, 0, 0, c);
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

function updateBalls(canvas, balls, timeDiff, mousePos) {
  var context = canvas.getContext('2d');
  var collisionDamper = 0.3;
  var floorFriction = 0.0005 * timeDiff;
  var mouseForceMultiplier = 1 * timeDiff;
  var restoreForce = 0.002 * timeDiff;
  var eps = 0;

  for(var n = 0; n < balls.length; n++) {
    var ball = balls[n];
    // set ball position based on velocity
    ball.y += ball.vy;
    ball.x += ball.vx;

    // restore forces
    if(ball.x > ball.origX + eps) {
      ball.vx -= restoreForce;
    }
    else if (ball.x < ball.origX - eps) {
      ball.vx += restoreForce;
    }
    if(ball.y > ball.origY + eps) {
      ball.vy -= restoreForce;
    }
    else if(ball.y < ball.origY - eps) {
      ball.vy += restoreForce;
    }

    // mouse forces
    var mouseX = mousePos.x;
    var mouseY = mousePos.y;

    var distX = ball.x - mouseX;
    var distY = ball.y - mouseY;

    var radius = Math.sqrt(Math.pow(distX, 2) + Math.pow(distY, 2));

    var totalDist = Math.abs(distX) + Math.abs(distY);

    var forceX = (Math.abs(distX) / totalDist) * (1 / radius) * mouseForceMultiplier;
    var forceY = (Math.abs(distY) / totalDist) * (1 / radius) * mouseForceMultiplier;

    if(distX > 0) {// mouse is left of ball
      ball.vx += forceX;
    }
    else {
      ball.vx -= forceX;
    }
    if(distY > 0) {// mouse is on top of ball
      ball.vy += forceY;
    }
    else {
      ball.vy -= forceY;
    }

    // floor friction
    if(ball.vx > 0) {
      ball.vx -= floorFriction;
    }
    else if(ball.vx < 0) {
      ball.vx += floorFriction;
    }
    if(ball.vy > 0) {
      ball.vy -= floorFriction;
    }
    else if(ball.vy < 0) {
      ball.vy += floorFriction;
    }

    // floor condition
    if(ball.y > (canvas.height - ball.radius)) {
      ball.y = canvas.height - ball.radius - 2;
      ball.vy *= -1;
      ball.vy *= (1 - collisionDamper);
    }

    // ceiling condition
    if(ball.y < (ball.radius)) {
      ball.y = ball.radius + 2;
      ball.vy *= -1;
      ball.vy *= (1 - collisionDamper);
    }

    // right wall condition
    if(ball.x > (canvas.width - ball.radius)) {
      ball.x = canvas.width - ball.radius - 2;
      ball.vx *= -1;
      ball.vx *= (1 - collisionDamper);
    }

    // left wall condition
    if(ball.x < (ball.radius)) {
      ball.x = ball.radius + 2;
      ball.vx *= -1;
      ball.vx *= (1 - collisionDamper);
    }
  }
}

function clone(obj) {
  if (obj == null || typeof obj != 'object') {
    return obj;
  }
  var copy = obj.constructor();
  for (var attr in obj) {
    if (obj.hasOwnProperty(attr)) {
      copy[attr] = obj[attr];
    }
  }
  return copy;
}

function Ball(x, y, r, vx, vy, color) {
  this.x = x;
  this.y = y;
  this.vx = vx;
  this.vy = vy;
  // 
  this.color = color;
  this.origX = x;
  this.origY = y;
  this.radius = r;
  //
  this.alpha = 1;
  this.alive = 1;
  //
  this.update = function () {
    if (this.alive == 0) {
      this.radius *= 1.005;
      this.alpha *= 0.98;
      if (this.alpha < 0.005) {
        this.alpha = 0;
        this.radius = 0;
        this.alive = -1;
      }
    }
  }
  this.demon = function (tar) {
    this.x = tar.x;
    this.y = tar.y;
    this.vx = tar.vx;
    this.vy = tar.vy;
  }
}

var g_animateId = -1;
var g_balls = [];

function animate(canvas, balls, lastTime, mousePos, animateId) {
  if (animateId != g_animateId) {
    return;
  }
  var context = canvas.getContext('2d');
  var curtime = (new Date()).getTime();
  var timeDiff = curtime - lastTime;
  lastTime = curtime;
  updateBalls(canvas, balls, timeDiff, mousePos);

  context.clearRect(0, 0, canvas.width, canvas.height);
  for(var n = 0; n < balls.length; n++) {
    var ball = balls[n];
    context.beginPath();
    context.arc(ball.x, ball.y, ball.radius, 0, 2 * Math.PI, false);
    context.fillStyle = ball.color;
    context.globalAlpha = ball.alpha;
    context.fill();
  }

  for (var i = 0; i < balls.length; ++i) {
    balls[i].update();
    if (balls[i].alive == -1) {
      balls[i] = balls[balls.length-1];
      balls.pop();
      --i;
    }
  }

  requestAnimFrame(function() {
    animate(canvas, balls, lastTime, mousePos, animateId);
  });
}

function orderBalls(balls) {
  var hm = {};
  for (var i = 0; i < balls.length; ++i) {
    var ball = balls[i];
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

function animateNewsBalls(oldBalls, newBalls) {
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

function funCanvas() {
  var canvas = document.getElementById('bouncingBalls');
  var text = document.getElementById('bouncingBalls.text').value;
  var fontsize = document.getElementById('bouncingBalls.fontsize').value;
  var ballRadius = document.getElementById('bouncingBalls.ballRadius').value;
  var dynamic = document.getElementById('bouncingBalls.dynamicBalls').checked;
  ballRadius = Math.floor(parseFloat(ballRadius));
  var balls = renderBalls(canvas, text, fontsize, ballRadius);

  if (dynamic) {
    balls = animateNewsBalls(g_balls, balls);    
  }
  g_balls = balls;

  var time = (new Date()).getTime();
  var mousePos = {
    x: 1e9,
    y: 1e9
  };
  canvas.addEventListener('mousemove', function(evt) {
    var pos = getMousePos(canvas, evt);
    mousePos.x = pos.x;
    mousePos.y = pos.y;
  });
  canvas.addEventListener('mouseout', function(evt) {
    mousePos.x = 1e9;
    mousePos.y = 1e9;
  });

  ++g_animateId;
  animate(canvas, balls, time, mousePos, g_animateId);
}

window.onload = function () {
  window.requestAnimFrame = (function(callback) {
    return window.requestAnimationFrame || window.webkitRequestAnimationFrame 
      || window.mozRequestAnimationFrame || window.oRequestAnimationFrame 
      || window.msRequestAnimationFrame || function(callback) {
      window.setTimeout(callback, 1000 / 30);
    };
  })();
  funCanvas();
}
