window.addEventListener("load", () => {
    //adds an evert listener to the tab click - this stops all api requests happening on page load and fires only once the
    //tab has been clicked
    window.mobilenav = document.querySelector("[data-mobnav]")

    //charts array for response times
    window.charts = []

    // check the getting-started tab for responses
    get_response(document.querySelector("#getting_started"))

    document.querySelectorAll("[data-tab]").forEach(tab_val => {
        // this is the actual content el that needs to have the page setup run on it
        let tab_content_el = document.getElementById(tab_val.getAttribute("data-tab"))
        // bootstraps show event for tabs
        tab_val.addEventListener('show.bs.tab', function (event) {
            close_mobile_nav()
            //
            //scroll to top on click
            window.scrollTo({top: 0, behavior: "smooth"})
            //mark it as done so we dont have it run each time the tab is clicked
            if (!tab_val.hasAttribute("data-loaded")) {
                //page setups
                setup_page(tab_content_el)
                tab_val.setAttribute("data-loaded", "")
            }
        })

        tab_val.addEventListener('shown.bs.tab', function (event) {
            // apex charts are not rendering properly needs to have a bump start here. Horrible fix but
            // cant work it out currently.
            if (!tab_val.hasAttribute("data-shown")) {
                let chart_id = tab_val.getAttribute("data-bs-target") + "_chart"
                window["charts"][chart_id.replace("#", "")].render()
                tab_val.setAttribute("data-shown", "")
            }
        })


    })

    // setup close and open buttons
    document.querySelector("[data-close]").addEventListener("click", (e) => {
        close_mobile_nav()
    })
    //    setup open buttons
    document.querySelector("[data-open]").addEventListener("click", (e) => {
        open_mobile_nav()
    })
})

function open_mobile_nav() {
    mobilenav.classList.remove("left_mobile_nav")
}

function close_mobile_nav() {
    mobilenav.classList.add("left_mobile_nav")
}

const zip = (...rows) => [...rows[0]].map((_, c) => rows.map(row => row[c]))

function get_response(tab_content_el) {
    // tab_content_el = the current tab content
    let response_els = tab_content_el.querySelectorAll("[data-example]")
    response_els.forEach(value => {
        let url = value.getAttribute("data-example")
        let parameter = value.getAttribute("data-param")
        let val = value.getAttribute("data-val")

        //if the paras have pipes then its expected to be a list -> build the param by splitting
        if (parameter.includes("¬")) {
            // you can add additional parameters to the data-parameter file and split with the ¬ character. It was | but was interfering with the postcode split
            let params = parameter.split("¬")
            let vals = val.split("¬")
            let param_ar = zip(params, vals)
            let new_q_string = ""
            param_ar.forEach(value => {
                new_q_string = new_q_string + value[0] + "=" + value[1] + "&"
            })
            url = `/api/${url}?${new_q_string.slice(0, -1)}`
        } else {
            url = `/api/${url}?${parameter}=${val}`
        }

        // this collects the data attribute for wait time and times run - this is used for some of the error responses
        // it defaults if not found
        let wait_time = value.hasAttribute("data-wait") ? value.getAttribute("data-wait") : 0
        let times_run = value.hasAttribute("data-times") ? value.getAttribute("data-times") : 1

        // wait for run
        setTimeout(() => {
            //run times
            for (let i = 0; i < times_run; i++) {
                fetch(url)
                    .then(async response => {
                        let data = await response.json()
                        value.innerHTML = "<pre>" + `<kbd style="font-size: 1.3rem">${response.status}</kbd><br><br>` + "<code>" + js_beautify(JSON.stringify(data)) + "</code></pre>"
                        hljs.highlightAll()
                    })
            }

        }, wait_time)

    })
}

function setup_inputs(tab_content_el) {
    // tab_content_el = the current tab content

    //get all input els
    let response_els = tab_content_el.querySelectorAll("[data-base]")
    //loop all
    response_els.forEach(main_el => {
        // get url
        let url = main_el.getAttribute("data-base")
        // get search
        let search_button = tab_content_el.querySelector(`[data-searchit='${url}']`)
        let code_el = tab_content_el.querySelector(`[data-codeit='${url}']`)
        //set check for keyup search val remove disabled from search button

        let type_els = tab_content_el.querySelectorAll(`[data-typeit='${url}']`)
        type_els.forEach(type_element => {
            ["click", "keyup"].forEach(action => {
                type_element.addEventListener(action, (e) => {
                    validate_all(url, type_element.getAttribute("data-typeit"), search_button, code_el, main_el)
                })
            })
        })

        //on click do the fetch
        search_button.addEventListener("click", () => {
            fetch(`/api/${url}${build_params(main_el)}`)
                .then(async response => {
                    let data = await response.json()
                    let output_el = document.querySelector(`[data-tryit='${url}']`)
                    output_el.innerHTML = `<kbd style="font-size: 1.3rem">${response.status}</kbd><br><br>` + "<code>" + js_beautify(JSON.stringify(data)) + "</code>"
                    output_el.scrollIntoView()
                    hljs.highlightAll()
                }).catch(resp => {
                console.log(resp)
            })
        })


    })
}

function build_params(main_el) {
    // builds the parameters for the query with the inputs as param values
    let name = main_el.getAttribute("data-typeit")
    let params = ""
    let add_this_value = false
    let param_name = ""
    let param_value = ""
    document.querySelectorAll(`[data-typeit='${name}']`).forEach(value => {
        param_name = value.getAttribute("data-param")
        add_this_value = false
        // checks the fields to see if needs to be added or not by type
        if (value.tagName === "INPUT" && (value.type === "text" || value.type === "number")) {
            param_value = value.value
            if (param_value && param_value !== "") {
                add_this_value = true
            }
        } else if (value.tagName === "INPUT" && value.type === "checkbox") {
            if (value.checked) {
                param_value = 1
                add_this_value = true
            }
        } else if (value.tagName == "SELECT") {
            param_value = value.value
            add_this_value = true
        }
        // add value only if allowed and check for ? & etc
        params = params + (add_this_value ? (params.includes("?") ? `&${param_name}=${param_value}` : `?${param_name}=${param_value}`) : "")
    })
    return params.replaceAll(" ", "+")
}

function validate_all(url, type, button, code, main_el) {
    // validates each input box for the "Try it" section. Only worries if the input is REQUIRED
    let items = 0
    let passed = 0
    main_el.parentElement.parentElement.querySelectorAll(`[data-typeit='${type}']`).forEach(value => {
        if (value.hasAttribute("required")) {
            let item_valid = value.checkValidity()
            items++
            if (item_valid) {
                passed++
            }
        }
    })
    //enables the request run button if reqs are met
    if (items == passed) {
        button.removeAttribute("disabled")
    } else {
        button.setAttribute("disabled", "")
    }
    // always builds the url regardless
    code.innerText = `https://postcoderoonie.co.uk/${url}${build_params(main_el)}`

}

function load_ms_total(url_el) {
    // queries the database for the avg ms response time and count - only when the tab has
    // been clicked for the first time. Each subsequent tab open does nothing.
    let endpoint = url_el.querySelector("[data-base]").getAttribute("data-base")
    let ms_val = document.getElementById("ms_" + endpoint)
    let count_val = document.getElementById("count_" + endpoint)
    fetch(`/api/api-use-review/${endpoint}`).then(resp => resp.json()).then(
        data => {
            ms_val.innerText = data["avg"]
            count_val.innerText = data["count"]
        }
    )
}

function add_request_chart(url_el) {
    // request the chart data
    let endpoint = url_el.querySelector("[data-base]").getAttribute("data-base")
    let chart_val = document.getElementById(endpoint + "_chart")

    fetch(`/api/api-response/${endpoint}`).then(resp => resp.json()).then(
        data => {
            generate_chart(chart_val, data["data"], data["time"])
        }
    )
}

function generate_chart(chart_el, data, time) {
    "generate the chart data"
    let options = {
        series: [{
            name: "response",
            data: data
        }],
        chart: {
            height: 350,
            type: 'line',
            zoom: {
                enabled: false
            }
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth'
        },
        colors: ['#E26D5C'],
        title: {
            text: 'Response time (ms)',
            align: 'left'
        },
        grid: {
            row: {
                colors: ['#f3f3f3', 'transparent'], // takes an array which will be repeated on columns
                opacity: 0.5
            },
        },
        xaxis: {
            type: 'numeric',
            categories: time,
            show: false
        },
        annotations: {
            position: 'front',
            xaxis: [{
                x: 1800,
                borderColor: '#c2c2c2',
                fillColor: '#c2c2c2',
                opacity: 0.3,
                width: '100%',
                label: {
                    borderColor: '#c2c2c2',
                    borderWidth: 1,
                    borderRadius: 2,
                    text: "HERRRRR"
                }
            }]
        }
    };

    window["charts"][chart_el.id] = new ApexCharts(chart_el, options)

}

function setup_page(tab_content_el) {
    //    sets up the tab - this runs only when the tab is clicked for the first time, speeding up initial
    //    page load as all the ajax calls etc do not happen in one go.

    // example responses load
    get_response(tab_content_el)
    // try your self button setup etc
    setup_inputs(tab_content_el)
    // ms and count resopnse times
    load_ms_total(tab_content_el)
    // chart for ms respose time
    add_request_chart(tab_content_el)

}