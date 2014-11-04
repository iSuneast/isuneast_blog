
function sign(v) {
  if (v > 0) {
    return 1;
  } else if (v < 0) {
    return -1;
  } else {
    return 0;
  }
}

function randomInt(minV, maxV) {
  return Math.floor(Math.random() * (maxV - minV)) + minV;
}

function RandomPickHashSet() {
  this.hm = {};
  this.vec = [];
  this.find = function (v) {
    return this.hm.hasOwnProperty(v);
  }
  this.add = function(v) {
    id = this.vec.length;
    this.vec.push(v);
    this.hm[v] = id;
  }
  this.pick = function() {
    return this.vec[randomInt(0, this.vec.length)];
  }
  this.remove = function(v) {
    if (!this.find(v)) {
      return;
    }
    id = this.hm[v];
    tv = this.vec[this.vec.length-1];
    this.vec[id] = tv;
    this.hm[tv] = id;

    this.vec.pop();
    delete this.hm[v];
  }
  this.size = function() {
    return this.vec.length;
  }
}

function RandomPickHashMap() {
  this.hm = {};
  this.vec = [];
  this.find = function(key) {
    return this.hm.hasOwnProperty(key);
  }
  this.get = function(key) {
    if (!this.find(key)) {
      return null;
    }
    id = this.hm[key];
    return this.vec[id][1];
  }
  this.add = function(key, val) {
    id = this.vec.length;
    this.vec.push([key, val]);
    this.hm[key] = id;
  }
  this.pick = function() {
    return this.vec[randomInt(0, this.vec.length)][0];
  }
  this.pickVal = function() {
    return this.vec[randomInt(0, this.vec.length)][1];    
  }
  this.remove = function(key) {
    if (!this.find(key)) {
      return;
    }
    id = this.hm[key];
    tmp = this.vec[this.vec.length-1];
    this.vec[id] = tmp;
    this.hm[tmp[0]] = id;

    this.vec.pop();
    delete this.hm[key];
  }
  this.size = function() {
    return this.vec.length;
  }
}
