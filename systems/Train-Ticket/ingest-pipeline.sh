#!/bin/bash

curl -X PUT "localhost:9200/jaeger-span-`date +'%Y-%m-%d'`"
curl -X PUT "localhost:9200/jaeger-span-`date -d '+1 day' +'%Y-%m-%d'`"


curl -XPUT "http://localhost:9200/_ingest/pipeline/jaeger" -H 'Content-Type: application/json' -d'{    "description": "Rewrite span",    "processors": [      {"script": {        "lang": "painless",        "source": "\n          ctx.traceId= ctx.traceID;\n          ctx.id= ctx.spanID;\n          ctx.timestamp= ctx.startTime;\n          ctx.name= ctx.process.serviceName + \"_\" + ctx.operationName;\n          for (int i = 0; i < ctx.tags.length; ++i) {\n            if(ctx.tags[i].key == \"span.kind\"){\n              ctx.kind = ctx.tags[i].value.toUpperCase();\n            }\n            if(ctx.tags[i].key == \"experiment\"){\n              ctx.experiment = ctx.tags[i].value;\n            }\n          }\n          for (int i = 0; i < ctx.references.length; ++i) {\n            if(ctx.references[i].refType == \"CHILD_OF\"){\n              ctx.parentId = ctx.references[i].spanID;\n            }\n          }\n        "      }}    ]  }'
curl -XPUT "http://localhost:9200/jaeger-span-*/_settings" -H 'Content-Type: application/json' -d'{    "index" : {        "default_pipeline" : "jaeger"    }}'
