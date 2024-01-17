# Caddylyser

Caddylyser is a log analyser. Caddylyser visualises logs live in your browser, so you see new logs as they happen. Caddylyser is modular, meaning you can easily create and add your own addons that parse different types of logs.

## Getting Started

### Caddyfile

Add the following to the top of your Caddyfile:

```
{
    log {
        output file /var/log/caddy/access.log {
            roll_size 10gb
            roll_keep 20
            roll_keep_for 720h
        }
        include http.log.access
    }
}
```

Then, add `log` within each site block you wish to analyse. For example:

```
example.com {
    log
    respond "Hello, World!"
}
```

### Caddylyser Backend

Copy `caddylyser.py` to your log directory, in this case, `/var/log/caddy/`. To ensure everything is working correctly, you can run the Python file natively, it should start printing JSON after a couple of seconds. After testing the Python code directly, install [websocketd](http://websocketd.com/).

To start the backend, run:

```
websocketd --port=5901 /usr/bin/python3 index.py
```

To keep the backend running in the background, run it as a cronjob instead. First run:

```
crontab -e
```

Then input the following into the last line:

```
@reboot websocketd --port=5901 /usr/bin/python3 index.py
```

### Caddylyser Frontend

To set up the frontend, edit index.html, and set the `ws_endpoint` variable to your web socket. Ensure `modules.json` is in the same directory as index.html. You can now open index.html in your browser and start analysing!

### modules.json (Optional)

Each session on the dashboard has its own sandbox. Customisations only apply for that session. If you'd like to hardcode the default modules shown as well as their styling, you can edit the modules.json file. By default, 2 modules fit on a page, using the doughnut style. You can edit modules.json to change the default modules shown, the type of chart they are, and their size.

```
{
    "status":  {
        "type": "doughnut",
        "size": "30%"
    },
    "request.uri":  {
        "type": "line",
        "size": "200px"
    }
}
```

## Features

Caddylyser was inspired by [GoAccess](https://goaccess.io). I've always loved the ease of use they provide for quickly analysing logs. But, I had a few things I didn't like about it, so I made this. All features below are based on my grievances with GoAccess.

### Modules

Caddylyser has a built-in module system. Modules are sourced from metrics that appear in your logs. For example, there is a `request.host` module, which shows numbers on a per-host basis. Modules are Lego-like. You can choose to include or exclude any module from appearing in the dashboard. This allows for your dashboard to show only the metrics you care about, without you having to dig through the panel trying to find what you need.
<img width="1035" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/1278dbc3-e6e5-4dfe-9adc-699940ab3a50">

### Automatic Module Gathering

Modules are automatically created. They just _appear_. As Caddylyser processes more logs, it finds new modules that might be of interest. For example, each request and response header seen in the logs gets given its own module. It's up to you if you use it or not. This creates great extensibility no matter your use case. For example, if you use Cloudflare, you will see geo-location modules start appearing. Another great example is cache. When you cache an endpoint you're passing certain headers, for example, `Cache-Control`. Caddylyser will automatically create a module called `resp_headers.Cache-Control` showing your cache coverage after it sees the header in your logs.
<img width="490" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/0827c1b1-00f2-418c-a6c0-0f507e68adc7"><img width="490" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/f192ea67-69a5-46fa-8975-ebfd6ffe88aa">

### Customisation

Caddylyser allows you to change the type of graph you're looking at on a per-module basis. You are able to choose between bar, line, pie, and doughnut charts.
<img width="1309" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/b12e50a3-541a-4914-88fd-2f6e42a7bc4a">
<img width="222" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/27cb22b2-a500-4c09-b714-814f9b097354">
<img width="222" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/b52208fe-d403-4347-8575-0baee69fffd5">
<img width="176" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/47db21f4-e2c1-4b1e-8661-23112398da1e">
<img width="206" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/d7b8a0f1-b111-4707-a50f-c088b8ee44e5">

Caddylyser also allows you to change the size of each graph. This means you could put 1 chart at 100% width, with 2 under it, each at 50%. You could set one chart to 70% and another to 30%. Whatever your heart desires.
<img width="1775" alt="image" src="https://github.com/QuixThe2nd/Caddylyser/assets/25378634/5b604586-bb57-4a3e-8eaf-2fa28a367c9e">

### Addons

With Caddylyser, you can create an addon that parses a new type of log in minutes. An addon is simply a Python file. To make your own, copy and rename the `boilerplate.py` file in `addons/`.

Addons can be invoked in 2 ways, matching and handling. When Caddylyser runs, it will call `match()` in your addon, and pass a single line from logs (string). The match function shall return True if the log format is compatible with your addon, and false otherwise. It is crucial that this function is fast as it will lower log parse times. Once a match() is found, Caddylyser will call `handler()` with the same log. Handler must return an object `{}`. This object can have as many dimensions it needs, just ensure it is compatible with the log flattener. You do not need to worry about error handling, you can throw errors directly in your addon. Caddylyser will automatically handle exceptions.

Caddylyser addons are super simple to import too, literally just drop the file into the addons folder and Caddylyser will start using that for future compatible logs!

### Save States

Caddylyser writes the latest metrics to a resume file for later. This means if Caddylyser stops running, its progress parsing the logs has been saved. This also means when Caddy periodically deletes old access logs, Caddylyser still has a (much smaller) record, so you can view analytics from logs that were deleted months ago.

### Backlog Parsing

One of my favourite features about Caddylyser is the backlog parsing. When you first run Caddylyser, instead of making you wait for all logs to be initially parsed, everything works as usual. You can use the Caddylyser and see live analytics, however delayed. Caddylyser will just keep scanning, starting from the oldest log, till it eventually reaches the end of the log file.

## Remarks

I hope you find this project useful in some way. I'm not a designer, so the UI on the app is unfinished. If you find Caddylyser useful or just like the idea of it, please considering helping improve the design :)
