// import balls
document.write('<script src="./static/balls.js"></script>');

function animateStartButton(canvas, timeDiff, mousePos) {
  if (!gameConf.drawStartButton()) {
    return ;
  }

  var context = canvas.getContext('2d');
  var balls = gameConf.startButtonBalls;
  var moveForceMul = 0.5;
  updateBalls(canvas, balls, timeDiff, mousePos, moveForceMul);

  // outer
  balls[0].draw(context);
  // inner
  balls[1].draw(context);
  // triangle
  for (var i = 0, offset = 2; i < 3; ++i) {
    if (i == 0) {
      context.beginPath();      
      context.moveTo(balls[i+offset].x, balls[i+offset].y);
      context.fillStyle = balls[i+offset].color;
      context.globalAlpha = balls[i+offset].alpha;
    } else {
      context.lineTo(balls[i+offset].x, balls[i+offset].y);
    }
  }
  context.closePath();
  context.fill();
}

function animateBalls (canvas, timeDiff, mousePos) {
  var balls = gameConf.balls;

  var context = canvas.getContext('2d');
  updateBalls(canvas, balls, timeDiff, mousePos);
  for(var i = 0; i < balls.length; ++i) {
    var ball = balls[i];
    ball.fadeout();
    if (ball.alive == -1 || ball.outside(canvas)) {
      // timer style base on the latest removed ball
      this.timerStyle = ball.color;
      balls[i] = balls[balls.length-1];
      balls.pop();
      --i;
    } else {
      context.beginPath();
      context.arc(ball.x, ball.y, ball.radius, 0, 2 * Math.PI, false);
      context.fillStyle = ball.color;
      context.globalAlpha = ball.alpha;
      context.fill();
    }
  }
}

function animateTimer (canvas, timeDiff, mousePos) {
  if (!gameConf.gameMode) {
    return ;
  }
  if (gameConf.clearTime != null) {
    timeDiff = gameConf.clearTime;
  } else if (gameConf.balls.length == 0) {
    gameConf.clearTime = timeDiff;
  }

  text = '';
  text += ' Balls: ' + gameConf.balls.length + '/' + gameConf.numBalls;
  text += ' DiDa: ' + (timeDiff / 1000.).toFixed(1);
  if (gameConf.clearTime != null) {
    text += '              ' + 'Sooooooo easy!!!';
  }

  // timerStyle base on nearest balls's color
  /*
  var dist = 1e9;
  for (var i = 0; i < balls.length; ++i) {
    var curDist = balls[i].sqrDist(mousePos.x, mousePos.y);
    if (dist > curDist) {
      dist = curDist;
      this.timerStyle = balls[i].color;
    }
  }
  */
  var context = canvas.getContext('2d');
  context.font = '30px Kranky';
  context.textAlign = 'left';
  context.globalAlpha = 1;
  if (this.timerStyle != null) {
    context.fillStyle = this.timerStyle;
  }
  context.fillText(text, 3, 33);
}

function animate (canvas, lastTime, mousePos) {
  var context = canvas.getContext('2d');
  var curTime = (new Date()).getTime();
  // timeDiff: at most 100 ms
  var timeDiff = Math.min(100, curTime - lastTime);
  var escapedTime = gameConf.escapedTime(curTime);
  lastTime = curTime;

  // clear
  context.clearRect(0, 0, canvas.width, canvas.height);
  if (gameConf.gameMode) {
    drawText(canvas, gameConf.text, gameConf.fontsize, 0.1);
  }
  animateBalls(canvas, timeDiff, mousePos);
  animateStartButton(canvas, timeDiff, mousePos);
  animateTimer(canvas, escapedTime, mousePos);

  requestAnimFrame(function() {animate(canvas, lastTime, mousePos);});
}

function updateCanvas() {
  var canvas = document.getElementById('bouncingBalls');
  var text = document.getElementById('bouncingBalls.text').value;
  var fontsize = document.getElementById('bouncingBalls.fontsize').value;
  var ballRadius = document.getElementById('bouncingBalls.ballRadius').value;
  ballRadius = Math.floor(parseFloat(ballRadius));
  var gameMode = document.getElementById('bouncingBalls.gameMode').checked;
  gameConf.initGame(canvas, text, fontsize, ballRadius, gameMode);

  return canvas;
}

window.onload = function () {
  window.requestAnimFrame = (function(callback) {
    return window.requestAnimationFrame || window.webkitRequestAnimationFrame 
      || window.mozRequestAnimationFrame || window.oRequestAnimationFrame 
      || window.msRequestAnimationFrame || function(callback) {
      window.setTimeout(callback, 1000 / 25);
    };
  })();
  gameConf.init();

  var canvas = updateCanvas();
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
  canvas.addEventListener('mousedown', function(evt) {
    var pos = getMousePos(canvas, evt);
    gameConf.onClick(pos);
  });

  var time = (new Date()).getTime();
  animate(canvas, time, mousePos);
}
