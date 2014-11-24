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
    this.sources = {};          // node_id -> Source (allows for panic)

     // user-controllable parameters
     this.params = {
         speed: 0.3,
         target: 0.1,
         sounds: "s2",
         mode: "down",
         net: false
     };
     this.SPEED_MAX = 50;
     this.TARGET_MAX = 20;

    this.nodes = spec.nodes;
    this._edgespec = spec.edges;

    // W & H are the effective size of the graph.
    // However, due to diferent screen sizes and backing scales, the
    // actual size of the canvas may be considerably different.
    this.W = 1200;
    this.H = 1240;

    // Use document w/h to compute a display size
    var max_display_w = document.body.clientWidth - 300; // 300 is the sidebar size.
    var max_display_h = document.body.clientHeight - 20; // 20 is a rough symmetry
    var display_ratio = Math.min(1, Math.min(
        max_display_w / this.W,
        max_display_h / this.H));
    this.px_ratio = display_ratio * BACKING_SCALE;
    this.VIEW_W = this.W * display_ratio;
    this.VIEW_H = this.H * display_ratio;

    this.$el = $("<div>");

    this.$canvas = $("<canvas>", {id: "base"})
        .attr({width: this.W * this.px_ratio,
              height:this.H * this.px_ratio})
        .css({width: this.VIEW_W,
                height:this.VIEW_H})
        .appendTo(this.$el);
    this.$overlay = $("<canvas>", {id: "overlay"})
        .attr({width: this.W * this.px_ratio,
               height:this.H * this.px_ratio})
        .css({width: this.VIEW_W,
                height:this.VIEW_H})
         .appendTo(this.$el);

    this.state_edges = [];
     this.nplaying = 0;

     this.clearburn();
     // this.load_sounds();

     // Start a timer to manage edges
     var T = 0.1;               // seconds
     this.edgeinterval = window.setInterval(function() {
         // Clear overlays
         that.$overlay
             .attr({width: that.W * that.px_ratio,
                    height:that.H * that.px_ratio})

         // ...and update
         var ctx = that.$overlay[0].getContext('2d');

         // burns
        if(that.params.mode === "burnbridges") {
            ctx.strokeStyle = "red";
            ctx.beginPath();
            for(var key in that._edgeburn) {
                var e = that._edgeburn[key];
                ctx.moveTo(e.a.pt[0]*that.px_ratio, e.a.pt[1]*that.px_ratio);
                ctx.lineTo(e.b.pt[0]*that.px_ratio, e.b.pt[1]*that.px_ratio);
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
                 ctx.moveTo(edgestate.edge.a.pt[0]*that.px_ratio, edgestate.edge.a.pt[1]*that.px_ratio);
                 var pos = edgestate.get_position();
                 ctx.lineTo(pos[0]*that.px_ratio, pos[1]*that.px_ratio);
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
            .offset({left: node.pt[0]*that.px_ratio-5,
                     top: node.pt[1]*that.px_ratio-5})
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
    if(this.nplaying >= (this.TARGET_MAX * this.params.target) || (node.id in this._nodeburn) || (node.id in this.sources)) {
        return;
    }
    this.nplaying += 1;

    var a = that.get_sound(node.nedges);

    var $node = that.$nodes[node.id];
    $node.addClass('playing');

    if(a) {
        // console.log("got sound", node.nedges, a);

        // Trigger through WebAudioAPI
        var source = myAudioContext.createBufferSource(); // creates a sound source
        source.buffer = a;
        source.connect(myAudioContext.destination);
        source.start(0);

        that.sources[node.id] = source;

        // XXX: Show playback progress!
        // 
        // a.ontimeupdate = function() {
        //     var percent = a.currentTime / a.duration;
        //     $node
        //         .css({width: 10*(1-percent),
        //               height:10*(1-percent)})
        //         .offset({left: node.pt[0]-5*(1-percent),
        //                  top: node.pt[1]-5*(1-percent)});
        // };
        source.onended = function() {    // XXX: 'bind'/'unbind'?
            delete that.sources[node.id];

            that.nplaying -= 1;

            if(that.params.mode === "burnbridges") {
                that._nodeburn[node.id] = node;
            }

            $node.removeClass('playing')
                .css({width: 10,
                      height:10})
                .offset({left: node.pt[0]*that.px_ratio-5,
                         top: node.pt[1]*that.px_ratio-5});

            (that.edges[node.id] || []).forEach(function(edge) {
                if(!(edge.id in that._edgeburn)) {
                    that.state_edges.push(new EdgeState(edge));
                }
            });
        };
        // a.play();
    }
    else {
        that.nplaying -= 1;

        if(that.params.mode === "burnbridges") {
            that._nodeburn[node.id] = node;
        }

        $node.removeClass('playing')
            .css({width: 10,
                  height:10})
            .offset({left: node.pt[0]*that.px_ratio-5,
                     top: node.pt[1]*that.px_ratio-5});

        (that.edges[node.id] || []).forEach(function(edge) {
            if(!(edge.id in that._edgeburn)) {
                that.state_edges.push(new EdgeState(edge));
            }
        });
    }
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
            ctx.moveTo(a.pt[0]*that.px_ratio, a.pt[1]*that.px_ratio);
            ctx.lineTo(b.pt[0]*that.px_ratio, b.pt[1]*that.px_ratio);
        })
    }
    ctx.stroke();
};
GRAPH.prototype.get_sound = function(n) {
    if(!this.snds.soundmap[n]) {
        console.log("no sound for", n);
        return;
    }
    var out = this.snds.soundmap[n][0];
    this.snds.soundmap[n] = this.snds.soundmap[n].slice(1).concat([out]);
    //return out.get_sound();
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
