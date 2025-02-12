# monitoring dashboards
backup of grafana dashboards


### setup
The nodejs package "wizzy" uses the grafana api to extract the dashboards and other data.

#### Install
> aerickson found this version was needed to get correct folders: https://github.com/mozilla-platform-ops/dashboards/pull/3
```
npm install -g github:johnsudaar/wizzy#971a8a1186d9b3036c87f96a339c4d9680d5b866
```


#### Configure
> create conf/wizzy.conf with auth:
```
wizzy set grafana url https://grafana.fqdn
wizzy set grafana username GRAFANA_USERNAME
wizzy set grafana password GRAFANA_PASSWORD
```


### backup process

```
rm -rf dashboards #remove to not duplicate renamed or moved
wizzy import dashboards
git add dashboards
git commit
```


### alternatives
* https://github.com/ysde/grafana-backup-tool
* Manually export and commit the json for dashboards
* https://github.com/esnet/gdg
  - recommended by wizzy authors
