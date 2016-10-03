module.exports = {
    getJson: function(name) {
        var json
        elements = document.getElementsByName(name)
        if (elements.length) {
            json = elements[0].text;
        }
        if (json) {
            try {
                return JSON.parse(json);
            } catch (_error) {
                console.warn("Error parsing json!");
                return console.warn(json);
            }
        }
    },
    combineObjs: function(obj1, obj2) {
        for (var attrName in obj2) {
            obj1[attrName] = obj2[attrName];
        }
    }
}