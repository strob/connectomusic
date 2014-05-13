var TOOLBAR = function(graph) {
    var that = this;
    this.g = graph;
    this.$el = $("<div>", {id: "toolbar"});

    this.g.ontrigger = function(nid) {
    }

    var bar = [
        {type: "select",
         name: "mode",
         options: ["down", "up", "bidir", "burnbridges"]},

        {type: "knob",
         name: "speed",
         min: 0,
         max: 250},

        {type: "knob",
         name: "target",
         min: 0,
         max: 100},

        {type: "buttongroup",
         buttons: ["saturate", "panic"]},
    ];

    var icon = function(name) {
        return "icon/" + name + ".png";
    }
    this.icon = icon;
    var icon_on = function(name) {
        return "icon/" + name + "_on.png";
    }
    this.icon_on = icon_on;

    var ux = function(x) {
        var $el;

        switch(x.type) {
        case "select" :
            $el = $("<div>")
                .addClass(x.name);
            x.options.forEach(function(opt) {
                $("<img>", {src: (that.g.params.mode === opt) ? icon_on(opt) : icon(opt)})
                    .addClass("option")
                    .addClass(opt)
                    .data("name", opt)
                    .appendTo($el)
                    .click(function() {
                        that.set(x.name, opt);
                    })
            });
            that.set(x.name, that.g.params[x.name]);

            break;
        case "toggle" :
            $el = $("<img>", {src: icon(x.name)})
                .addClass("toggle")
                .data("on", false)
                .click(function() {
                    that.toggle(x.name);
                });

            break;
        case "buttongroup" :
            $el = $("<div>").addClass("buttongroup");
            x.buttons.forEach(function(button) {
                $("<img>", {src: icon(button)})
                    .addClass("button")
                    .mouseover(function() {this.src = icon_on(button);})
                    .mouseout(function() {this.src = icon(button);})
                    .click(function() {
                        console.log(button);

                        if(that["on"+button]) {
                            that["on"+button]();
                        }
                    })
                    .appendTo($el);
            });
            break;
        case "knob" :
            $el = $("<canvas>")
                .addClass("knob")
                .addClass(x.name)
                .data("val", 0.5);
            (function($can) {
                var $img = $("<img>", {src: icon(x.name)})
                    .load(function() {
                        $can.attr({width: this.width,
                                   height: this.height});
                        $can.data("w", this.width);
                        $can.data("h", this.height);
                        $can.data("cx", this.width / 2);
                        $can.data("cy", 16); // hardcoded...
                        $can.data("r", 16);
                        $can.data("img", this);
                        var ctx = $can[0].getContext('2d');
                        ctx.drawImage(this, 0, 0);

                        that.turnKnob(x.name, that.g.params[x.name]); // initialize

                        $can.mousedown(function(ev) {
                            ev.preventDefault();
                            // start drag
                            var px = ev.clientX;
                            var py = ev.clientY;
                            window.onmousemove = function(ev) {
                                var dx = ev.clientX - px;
                                var dy = ev.clientY - py;

                                var val = $can.data("val");
                                val = Math.min(1, Math.max(0, val + dy / 100));
                                $can.data("val", val);

                                that.set(x.name, val);

                                px = ev.clientX;
                                py = ev.clientY;
                            }
                            window.onmouseup = function() {
                                // stop drag
                                window.onmousemove = undefined;
                                window.onmouseup = undefined;
                            }
                        });
                    });
            })($el)
            break;
        }
        return $el;
    }

    bar.forEach(function(b) {
        that.$el.append(ux(b));
    });
}
TOOLBAR.prototype.set = function(k, v, nobubble) {
    // update graph
    var old = this.g.params[k];
    if(old === v) {
        // no change
        return;
    }
    this.g.params[k] = v;

    if(this["on"+k]) {
        this["on"+k](v);
    }
};
TOOLBAR.prototype.toggle = function(k) {
    this.set(k, !this.g.params[k]);
};
TOOLBAR.prototype.onmode = function(v) {
    var that = this;
    this.$el.find(".mode .option").each(function(idx, opt) {
        if($(opt).data("name") === v) {
            opt.src = that.icon_on(v);
        }
        else {
            opt.src = that.icon($(opt).data("name"));
        }
    });
    // XXX: not always!
    this.g.clearburn();
    this.g.compute_edges();
};
TOOLBAR.prototype.onsaturate = function() {
    for(var i=0; i< (this.g.params.target * this.g.TARGET_MAX); i++) {
        var nid = Math.floor(Math.random() * this.g.nodes.length);
        this.g.trigger(this.g.nodes[nid]);
    }
};
TOOLBAR.prototype.onpanic = function() {
    this.g.state_edges = [];
    // for(var key in this.g.sounds) {
    //     this.g.sounds[key].forEach(function(a) {
    //         a.pause();
    //         a.currentTime = 0.0;
    //     });
    // }
    for(var key in this.g.sources) {
        this.g.sources[key].onended = null;
        this.g.sources[key].stop(0);
        delete this.g.sources[key];
    }
    $(".node")
        .removeClass("playing");
    this.g.clearburn();
    this.g.nplaying = 0;
};
TOOLBAR.prototype.turnKnob = function(name, val) {
    var $can = this.$el.find(".knob."+name);
    $can.data("val", val);
    // redraw
    $can.attr({width: $can.data("w"),
               height: $can.data("h")});
    var ctx = $can[0].getContext('2d');
    ctx.drawImage($can.data("img"), 0, 0);
    ctx.strokeStyle = "red";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo($can.data("cx"), $can.data("cy"));
    var pad = 0.1;
    var theta = $can.data("val")*2*Math.PI*(1-pad) - Math.PI/2;
    var lx = $can.data("cx") + $can.data("r") * Math.cos(theta);
    var ly = $can.data("cy") + $can.data("r") * Math.sin(theta);
    ctx.lineTo(lx, ly);
    ctx.stroke();
};
TOOLBAR.prototype.onspeed = function(val) {
    this.turnKnob("speed", val);
};
TOOLBAR.prototype.ontarget = function(val) {
    this.turnKnob("target", val);
};

var SOUNDS = function(N) {
    var that = this;
    this.N = N;                 // number of sounds

    this.soundmap = {};         // num -> [sound]
};
SOUNDS.prototype.add_buffer = function(nid, buf) {
    this.soundmap[nid] = (this.soundmap[nid] || []).concat([buf]);
}
