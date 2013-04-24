
var EDGE = function(a, b, id) {
    this.a = a;
    this.b = b;
    this.id = id;
    this.length = Math.sqrt(
        Math.pow(a.pt[0] - b.pt[0], 2) + 
        Math.pow(a.pt[1] - b.pt[1], 2));
};

var EdgeState = function(edge) {
    this.edge = edge;
    this.percentage = 0.0;
};
EdgeState.prototype.iterate = function(t, speed) {
    var npixels = t * speed;
    var dpercentage = npixels / this.edge.length;

    this.percentage += dpercentage;
    if(this.percentage > 1.0) {
        return true;
    }
    return false;
};
EdgeState.prototype.get_position = function() {
    var that = this;
    return [0, 1].map(function(X) {
        return that.edge.a.pt[X] + that.percentage*(that.edge.b.pt[X] - that.edge.a.pt[X]);
    });
};

var GRAPH = function(spec, snds) {
    var that = this;

    this.snds = snds;

     // user-controllable parameters
     this.params = {
         speed: 0.3,
         target: 0.1,
         sounds: "s2",
         mode: "down",
         net: false
     };
     this.SPEED_MAX = 250;
     this.TARGET_MAX = 100;

    this.nodes = spec.nodes;
    this._edgespec = spec.edges;

    this.W = 1200;
    this.H = 1240;

    this.$el = $("<div>");

    this.$canvas = $("<canvas>", {id: "base"})
        .attr({width: this.W,
              height:this.H})
        .appendTo(this.$el);
    this.$overlay = $("<canvas>", {id: "overlay"})
        .attr({width: this.W,
               height:this.H})
         .appendTo(this.$el);

    this.state_edges = [];
     this.nplaying = 0;

     this.clearburn();
     this.load_sounds();

     // Start a timer to manage edges
     var T = 0.1;               // seconds
     this.edgeinterval = window.setInterval(function() {
         // Clear overlays
         that.$overlay
             .attr({width: that.W,
                    height:that.H})

         // ...and update
         var ctx = that.$overlay[0].getContext('2d');

         // burns
        if(that.params.mode === "burnbridges") {
            ctx.strokeStyle = "red";
            ctx.beginPath();
            for(var key in that._edgeburn) {
                var e = that._edgeburn[key];
                ctx.moveTo(e.a.pt[0], e.a.pt[1]);
                ctx.lineTo(e.b.pt[0], e.b.pt[1]);
            }
            ctx.stroke();
        }
         ctx.strokeStyle = "cyan";
         ctx.beginPath();

         that.state_edges.forEach(function(edgestate, idx) {
             if(edgestate.iterate(T, that.params.speed*that.SPEED_MAX)) {
                 // Remove edge & trigger
                 // XXX: will "idx" be correct on the next iteration?
                 that.state_edges.splice(idx, 1);
                 // XXX: check against TARGET
                 that.trigger(edgestate.edge.b);

                 if(that.params.mode === "burnbridges") {
                     that._edgeburn[edgestate.edge.id] = edgestate.edge;
                 }

             }
             else {
                 ctx.moveTo(edgestate.edge.a.pt[0], edgestate.edge.a.pt[1]);
                 var pos = edgestate.get_position();
                 ctx.lineTo(pos[0], pos[1]);
             }
         });

         ctx.stroke();

     }, 1000*T);

    this.$nodes = [];

    this.nodes.forEach(function(node, idx) {
        // Add "id" to each node; used as key in "this.edges"
        node.id = idx;

        var $node = $("<div>")
            .addClass('node')
            .offset({left: node.pt[0]-5,
                     top: node.pt[1]-5})
            .click(function() {
                that.trigger(node);
                that.ontrigger(idx);
            })
            .appendTo(that.$el);
        that.$nodes.push($node);
    });

    this.compute_edges();
    this.draw_base();

};
GRAPH.prototype.ontrigger = function(nid) {
    // (Unimplemented) callback on *user-initiated* playback events.
    console.log("shouldn't be here");
};
GRAPH.prototype.clearburn = function() {
    this._edgeburn = {};       // id: edge
    this._nodeburn = {};       // id: node
};
GRAPH.prototype.trigger = function(node) {
    var that = this;

    // Only trigger if we're below target
    if(this.nplaying >= (this.TARGET_MAX * this.params.target) || (node.id in this._nodeburn)) {
        return;
    }
    this.nplaying += 1;

    var a = that.get_sound(node.nedges);
    var $node = that.$nodes[node.id];
    $node.addClass('playing');
    a.ontimeupdate = function() {
        var percent = a.currentTime / a.duration;
        $node
            .css({width: 10*(1-percent),
                  height:10*(1-percent)})
            .offset({left: node.pt[0]-5*(1-percent),
                     top: node.pt[1]-5*(1-percent)});
    };
    a.onended = function() {    // XXX: 'bind'/'unbind'?
        that.nplaying -= 1;

        if(that.params.mode === "burnbridges") {
            that._nodeburn[node.id] = node;
        }

        $node.removeClass('playing')
            .css({width: 10,
                  height:10})
            .offset({left: node.pt[0]-5,
                     top: node.pt[1]-5});

        (that.edges[node.id] || []).forEach(function(edge) {
            if(!(edge.id in that._edgeburn)) {
                that.state_edges.push(new EdgeState(edge));
            }
        });
    };
    a.play();

};
GRAPH.prototype.compute_edges = function() {
    var that = this;

    var BD = (this.params.mode === "burnbridges" || this.params.mode === "bidir");
    var UP = this.params.mode === "up";

    this.edges = {};
    this._edgespec.forEach(function(e, idx) {
        var a = that.nodes[e.a];
        var b = that.nodes[e.b];
        
        if(BD) {
            // Since these are the same edge in different directions,
            // the index is the same.
            _append(that.edges, a.id, new EDGE(a, b, idx));
            _append(that.edges, b.id, new EDGE(b, a, idx));
        }
        else {
            if((a.nedges < b.nedges && !UP) || (a.nedges > b.nedges && UP)) {
                // swap a and b
                var c = b;
                b = a;
                a = c;
            }
            _append(that.edges, a.id, new EDGE(a, b, idx));
        }
    });

};
GRAPH.prototype.draw_base = function() {
    var that = this;
    var ctx = this.$canvas[0].getContext('2d');
    ctx.strokeStyle = "#000";
    ctx.beginPath();
    for(var k in this.edges) {
        this.edges[k].forEach(function(edge) {
            var a = edge.a;
            var b = edge.b;
            ctx.moveTo(a.pt[0], a.pt[1]);
            ctx.lineTo(b.pt[0], b.pt[1]);
        })
    }
    ctx.stroke();
};
GRAPH.prototype.load_sounds = function() {
    var that = this;
    $.getJSON(this.params.sounds + '.json', {}, function(snd) {
        that.set_sounds(snd);
    });
};
GRAPH.prototype.set_sounds = function(snds) {
    this.sounds = {};
    for (var key in snds) {
        this.sounds[key] = snds[key].map(function(x) {
            var a = new Audio(x + '.ogg'); // XXX: or mp3!
            a.load();
            a.onload = function() {
                // XXX: Update visualization (?)
                console.log("Loaded!", x);
            }
            return a;
        });
    }
};
GRAPH.prototype.get_sound = function(n) {
    if(!(n in this.sounds)) {
        console.log('no sound for n', n);
        n = 19;
    }
    var out = this.sounds[n][0];
    this.sounds[n] = this.sounds[n].slice(1).concat([out]);
    return out;
};

        // UTILITY

function _append(d, k, v) {
    // Make or add to list
    if(d[k] === undefined) {
        d[k] = [];
    }
    d[k].push(v);
}