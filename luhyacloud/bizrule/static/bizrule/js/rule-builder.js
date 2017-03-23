(function($) {
    $.fn.ruleBuilder = function(options) {
        if(options == "data") {
            var builder = $(this).eq(0).data("RuleBuilder");
            return builder.collectData();
        } else {
            return $(this).each(function() {
                var newrule = new Rule_Builder(this, options)
                $(this).data("RuleBuilder", newrule);
            });
        }
    };

    Rule_Builder = function(element, options) {
        this.element = $(element);
        this.options = options;
        this.init();
    }

    Rule_Builder.prototype = {
        init: function() {
          this.fields = this.denormalizeOperators(this.options.variables.variables, this.options.variables.variable_type_operators);
          this.rule  = this.options.rule;
          this.images = this.options.images;
          var div_row = this.create_rule_pannel();
          this.element.html(div_row);
        },

        denormalizeOperators: function(variablesData, operators) {
            return $.map(variablesData, function(variable)
            {
              variable.operators = operators[variable.field_type];
              return variable;
            });
        },

        collectData: function() {
          return this.collectDataFromNode(this.element.find(".panel").first());
        },

        collectDatafromConditions: function(element) {
          // collect conditions
          var _this = this;
          var conditions = element.find(".conditions").first();
          var flag = null;
          var bucket = {"all":[], "any": [], "indicator": ""};
          conditions.children().each(function(){
            if ($(this).is(".form-group")) {
                // collect conditon clause
                var cond = {
                    "name":     $(this).find(".field").val(),
                    "operator": $(this).find(".operator").val(),
                    "value":    $(this).find(".value").val()
                };
                var andor    = $(this).find(".andor").val();
                if (flag == null) {
                    flag = converAndOr2AllAny(andor);
                    bucket["indicator"] = flag;
                }
                bucket[flag].push(cond);
                flag = converAndOr2AllAny(andor);
            }
            if ($(this).is(".panel")) {
                var combo_cond = _this.collectDatafromConditions($(this));
                var combo_andor = $(this).find(".andor").first().val();
                if (flag == null) {
                    flag = converAndOr2AllAny(combo_andor);
                    bucket["indicator"] = flag;
                }
                bucket[flag].push(combo_cond);
                flag = converAndOr2AllAny(combo_andor);
            }
          });

          return  mergeBucket2Conditions(bucket);
        },

        collectDatafromActions: function(element) {
          // collect action
          var actions = element.find(".actions").first();
          var acts = [];
          actions.children().each(function() {
            var act = {};
            if ($(this).is(".form-group")) {
                act["name"] = $(this).find(".func_name").val();
                var params = {};
                param_name_a = $(this).find(".param_name");
                param_val_a  = $(this).find(".param_val");
                for (var i=0; i<param_name_a.length; i++) {
                    params[param_name_a[i].innerText.slice(0,-1)] = param_val_a[i].value;
                }
                act["params"] = params
                acts.push(act);
            }
          });
          return acts;
        },

        collectDataFromNode: function(element) {
          // find panel-body.conditions, which including a few form-group and panel
          var output = {};

          output["conditions"] = this.collectDatafromConditions(element);
          output["actions"]    = this.collectDatafromActions(element);

          return output;
        },

        create_rule_pannel: function() {
          var _this = this;
          var div_row   = $("<div>", {"class": "row" });
          var div_clo   = $("<div>", {"class": "col-lg-12"});
          var div_panel = $("<div>", {"class": "panel panel-default"});
          var div_head  = $("<div>", {"class": "panel-heading", "text":"Conditions"});
          var div_body  = $("<div>", {"class": "panel-body conditions"});
          var conds = this.rule == null ? null : this.rule["conditions"];
          this.create_conditions(div_body, conds);
          var div_footer= $("<div>", {"class": "panel-footer", "text":"Actions"});
          var div_action= $("<div>", {"class": "panel-body actions"});
          div_action.append(this.create_actions());

          var div_right = $("<div>", {"class": "pull-right"});
          var btn_link_add = $("<div>", {"class": "btn btn-link btn-xs", "type":"button", "text":"Add Condition"});
          btn_link_add.click(function(e){
                e.preventDefault();
                var new_condition = _this.create_condition("and", null);
                div_body.append(new_condition);
          });

          var btn_link_sub_add = $("<div>", {"class": "btn btn-link btn-xs", "type":"button", "text":"Add Sub Condition"});
          btn_link_sub_add.click(function(e){
                e.preventDefault();
                var new_sub_condition = _this.create_sub_condition(null);
                div_body.append(new_sub_condition);
          });
          var btn_link_rm  = $("<div>", {"class": "btn btn-link btn-xs", "type":"button", "text":"Remove"});
          btn_link_rm.click(function(e) {
                e.preventDefault();
                div_row.parent().remove();
          });

          div_right.append(btn_link_add);
          div_right.append(btn_link_sub_add);
          div_right.append(btn_link_rm)
          div_head.append(div_right);

          div_panel.append(div_head);
          div_panel.append(div_body);
          div_panel.append(div_footer);
          div_panel.append(div_action);

          div_clo.append(div_panel);
          div_row.append(div_clo);
          return div_row;
        },

        create_select_name: function(cond) {
            var fields = this.fields;
            var select = $("<select>", {"class": "select-inline field"});
            for(var i=0; i < fields.length; i++) {
                var field = fields[i];
                var option = $("<option>", {
                    text: field.label,
                    value: field.name,
                    selected: cond == null ? false: cond.name == field.name
                });
                option.data("options", field.options);
                select.append(option);
            }
            select.data("cond", cond);
            return select;
        },

        create_select_operators: function(cond) {
            var select = $("<select>", {"class": "select-inline operator"});
            select.change(onOperatorSelectChange);
            if (cond != null) {

            }
            return select;
        },

        create_conditions: function(parent, rule) {
            if (rule != null) {
                var output;
                var andor_key = Object.keys(rule);
                andor = converAllAny2AndOr(andor_key[0]);
                // go through condition to build qian-zhou expression, and convert to zhong-zhui express
                var conds = rule[andor_key[0]]
                for (var i=0; i<conds.length; i++) {
                    if ( "operator" in conds[i] ) {
                        // this is a normal condition
                        parent.append(this.create_condition(andor, conds[i]))
                    }
                    if ( "any" in conds[i] || "all" in conds[i] ) {
                        // this is a sub condistions
                        parent.append(this.create_sub_condition(andor, conds[i]));
                    }
                }
            }
        },

        create_condition: function(andor, cond) {
            var form_group  = $("<div>", {"class": "form-group"});
            var select_name = this.create_select_name(cond);
            form_group.append(select_name);
            var select_op   = this.create_select_operators(cond);
            form_group.append(select_op);
            var select_value= $("<input>", {"class": "input-inline value"});
            form_group.append(select_value);
            select_name.change(onCondtionSelectChange.call(this, select_name, select_op, select_value));

            select_name.change();

            var select_andor= this.create_andor_select(andor);
            var btn_link_rm  = $("<div>", {"class": "btn btn-link btn-xs", "type":"button", "text":"Remove"});
            btn_link_rm.click(function(e) {
                e.preventDefault();
                form_group.remove();
            });

            form_group.append(select_andor);
            form_group.append(btn_link_rm);

            return form_group;
        },

        create_sub_condition: function(andor, rule) {
            var _this = this;
            var inner_andor = "and";
            if (rule != null) {
                andor_key = Object.keys(rule);
                inner_andor = converAllAny2AndOr(andor_key[0])
            }
            var div_panel = $("<div>", {"class": "panel panel-default"});
            var div_head  = $("<div>", {"class": "panel-heading", "text":"Conditions"});
            var div_body  = $("<div>", {"class": "panel-body conditions"});
            this.create_conditions(div_body, rule)
            var div_footer= $("<div>", {"class": "panel-footer"});

            var select_andor= this.create_andor_select(andor);
            div_footer.append(select_andor);

            var div_right = $("<div>", {"class": "pull-right"});
            var btn_link_add = $("<div>", {"class": "btn btn-link btn-xs", "type":"button", "text":"Add Condition"});
            btn_link_add.click(function(e){
                e.preventDefault();
                var new_condition = _this.create_condition(inner_andor, null);
                div_body.append(new_condition);
            });
            var btn_link_sub_add = $("<div>", {"class": "btn btn-link btn-xs", "type":"button", "text":"Add Sub Condition"});
            btn_link_sub_add.click(function(e){
                e.preventDefault();
                var new_sub_condition = _this.create_sub_condition(inner_andor, null);
                div_body.append(new_sub_condition);
            });
            var btn_link_rm  = $("<div>", {"class": "btn btn-link btn-xs", "type":"button", "text":"Remove"});
            btn_link_rm.click(function(e) {
                e.preventDefault();
                div_panel.remove();
            });

            div_right.append(btn_link_add);
            div_right.append(btn_link_sub_add);
            div_right.append(btn_link_rm)
            div_head.append(div_right);

            div_panel.append(div_head);
            div_panel.append(div_body);
            div_panel.append(div_footer);

            return div_panel;

        },

        create_andor_select: function(andor) {
            var select_andor= $("<select>", {"class": "select-inline andor"});
            select_andor.append($("<option>", {"value": "AND", "text": "AND", "selected": andor == "and"}));
            select_andor.append($("<option>", {"value": "OR", "text": "OR", "selected": andor == "or"}));
            return select_andor;
        },

        create_actions: function() {
            var output;
            if (this.rule == null) {
                output =  this.create_action(null);
            } else {
                for (var i=0; i<this.rule.actions.length; i++) {
                    output = this.create_action(this.rule.actions[i]);
                }
            }
            return output;
        },

        create_action: function(act) {
            var form_group  = $("<div>", {"class": "form-group"});
            form_group.data("act", act);
            var select_name = $("<select>", {"class": "select-inline func_name"});
            select_name.change(onFuncNameSelectChange);
            var actions = this.options.variables.actions;
            form_group.data("actions", actions);

            for (var i =0; i<actions.length; i++) {
                var option = $("<option>", {
                    text:  actions[i].label,
                    value: actions[i].name,
                });
                if (act != null && act.name == actions[i].name) {
                    option.prop("selected", true);
                }
                select_name.append(option);
            }
            form_group.append(select_name);

            var index = select_name.find("option:selected").index();
            if (act != null) {
                act_keys = Object.keys(act.params);
                for (var i=0; i<act_keys.length; i++) {
                    var select_label= $("<label>", {"class": "lable-inline param_name", "text": act_keys[i]+"=" });
                    form_group.append(select_label);

                    var select_value= $("<input>", {"class": "input-inline param_val", "value": act.params[act_keys[i]]});
                    form_group.append(select_value);
                }
            } else {
                for (var i=0; i<actions[index].params.length; i++) {
                    var select_label= $("<label>", {"class": "lable-inline param_name", "text": actions[index].params[i].label+"=" });
                    form_group.append(select_label);

                    var select_value= $("<input>", {"class": "input-inline param_val"});
                    form_group.append(select_value);
                }
            }
            return form_group;
        },

        operatorsFor: function(fieldName) {
          for(var i=0; i < this.fields.length; i++) {
            var field = this.fields[i];
            if(field.name == fieldName) {
              return field.operators;
            }
          }
        },

        get_field_type: function(fieldName) {
          for(var i=0; i < this.fields.length; i++) {
            var field = this.fields[i];
            if(field.name == fieldName) {
              return field.field_type;
            }
          }
        },
    };

    function onFuncNameSelectChange(e) {
        var $this = $(this);
        var container = $this.parent();
        var func_name = container.find(".func_name");
        var param_labels = container.find(".param_name");
        var param_values = container.find(".param_val");
        var option = $this.find(":selected");
        var index = func_name.find("option:selected").index();

        var act = container.data("act");
        var actions = container.data("actions");

        param_labels.each(function(){
            $(this).remove();
        });
        param_values.each(function(){
            $(this).remove();
        });

        var current_func_name = option.val();
        if (act != null && current_func_name == act.name) {
            act_keys = Object.keys(act.params);
            for (var i=0; i<act_keys.length; i++) {
                var select_label= $("<label>", {"class": "lable-inline param_name", "text": act_keys[i]+"=" });
                container.append(select_label);

                var select_value= $("<input>", {"class": "input-inline param_val", "value": act.params[act_keys[i]]});
                container.append(select_value);
            }
        } else {
            for (var i=0; i<actions[index].params.length; i++) {
                var select_label= $("<label>", {"class": "lable-inline param_name", "text": actions[index].params[i].label+"=" });
                container.append(select_label);

                var select_value= $("<input>", {"class": "input-inline param_val"});
                container.append(select_value);
            }
        }
    }
    function onOperatorSelectChange(e) {
        //var builder = this;
        var $this = $(this);
        var container = $this.parent();
        var fieldSelect = container.find(".field");
        var currentValue = container.find(".value");
        var val = currentValue.val();
        var option = $this.find(":selected");

        var cond = fieldSelect.data("cond");
        var param = cond == null ? "": cond["value"];

        // Clear errorMessages when switching between operator types
        $this.nextAll().each( function(index) {
            if ( $(this).attr('class') == 'errorMessage' ) {
                $(this).remove();
            }});
        switch(option.data("field_type")) {
          case "none":
            $this.after($("<input>", {"type": "hidden", "class": "value"}));
            break;
          case "text":
            $this.after($("<label class='errorMessage'></label>"));
            $this.after($("<input>", {"type": "text", "class": "value textInput", "value": param}));
            break;
          case "numeric":
            $this.after($("<label class='errorMessage'></label>"));
            $this.after($("<input>", {"type": "text", "class": "value numberInput", "value": param}));
            break;
          case "select":
            var select = $("<select>", {"class": "value"});
            var options = fieldSelect.find(":selected").data("options");
            for(var i=0; i < options.length; i++) {
              var opt = options[i];
              var option = $("<option>", {
                "text": opt,
                "value": opt,
                "selected": opt == param,
              });
              select.append(option);
            }
            $this.after(select);
            break;
          case "select_multiple":
            var options = fieldSelect.find(":selected").data("options");
            var selectLength = options.length > 10 ? 10 : options.length;
            var select = $("<select class='value' multiple size='" + selectLength + "''></select>");
            for(var i=0; i <options.length; i++) {
              var opt = options[i];
              select.append($("<option>", {"text": opt, "value": opt}));
            }
            $this.after(select);
            break;
        }
        currentValue.remove();
  }
    function onCondtionSelectChange(nameselect, opselect, valselect) {
        var builder = this;
        return function(e) {
            var operators = builder.operatorsFor($(e.target).val());
            opselect.empty();
            cond = nameselect.data("cond");
            for (var i=0; i<operators.length; i++) {
                var op = operators[i];
                var option = $("<option>", {
                    text: op.label || operator.name,
                    value: op.name,
                    selected: cond == null ? false : cond.operator == op.name
                });

                option.data("field_type", op.input_type)
                opselect.append(option);
            }
            opselect.change();
        }
    }
    function converAllAny2AndOr( mydata ) {
        if (mydata == "all") {
            return "and";
        }
        if (mydata == "any") {
            return "or";
        }
    }
    function converAndOr2AllAny( mydata ) {
        if (mydata == "and" || mydata == "AND") {
            return "all";
        }
        if (mydata == "or" || mydata == "OR") {
            return "any";
        }
    }
    function mergeBucket2Conditions(bucket) {
        var any_a = bucket["any"];
        var all_a = bucket["all"];
        if (any_a.length == 0) {
            return {"all": all_a};
        } else if (all_a.length == 0) {
            return {"any": any_a};
        } else {
            var output;
            switch(bucket["indicator"]) {
                case "any":
                    all_a.push({"any":any_a});
                    output = {"all": all_a};
                    break;
                case "all":
                    any_a.push({"all":all_a});
                    output = {"any": any_a};
                    break;
            }
            return output;
        }
    }

})(jQuery);