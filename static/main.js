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

function findBalls(context, width, height) {
  context.textBaseline = "top";
  context.font = "150px Lato";
  context.fillText("iSuneast", 70, 30);
  data = context.getImageData(0, 0, width, height).data;
  var radius = new function () {
    this.min = 9;
    this.max = 9;
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
  ccColor = [];
  for (var i = ccColor.length; i < cc.numCC; ++i) {
    var tmp;
    do {
      tmp = color.pickVal();
    } while (i > 0 && tmp == ccColor[i-1]);
    ccColor.push(tmp);
  }
  ccColor[0] = ccColor[1];
  console.log(ccColor);

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

function Ball(x, y, r, vx, vy, color) {
  this.x = x;
  this.y = y;
  this.r = r;
  this.vx = vx;
  this.vy = vy;
  this.color = color;
  this.origX = x;
  this.origY = y;
  this.radius = r;
}

function animate(canvas, balls, lastTime, mousePos) {
  var context = canvas.getContext('2d');

  // update
  var date = new Date();
  var time = date.getTime();
  var timeDiff = time - lastTime;
  updateBalls(canvas, balls, timeDiff, mousePos);
  lastTime = time;

  // clear
  context.clearRect(0, 0, canvas.width, canvas.height);

  // render
  for(var n = 0; n < balls.length; n++) {
    var ball = balls[n];
    context.beginPath();
    context.arc(ball.x, ball.y, ball.radius, 0, 2 * Math.PI, false);
    context.fillStyle = ball.color;
    context.fill();
  }

  // request new frame
  requestAnimFrame(function() {
    animate(canvas, balls, lastTime, mousePos);
  });
}

window.onload = function () {
  window.requestAnimFrame = (function(callback) {
    return window.requestAnimationFrame || window.webkitRequestAnimationFrame 
      || window.mozRequestAnimationFrame || window.oRequestAnimationFrame 
      || window.msRequestAnimationFrame || function(callback) {
      window.setTimeout(callback, 1000 / 60);
    };
  })();

  var canvas = document.getElementById('myCanvas');
  var context = canvas.getContext('2d');
  var balls = findBalls(context, canvas.width, canvas.height);
  var date = new Date();
  var time = date.getTime();
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
  animate(canvas, balls, time, mousePos);  
}
