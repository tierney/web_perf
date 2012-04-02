# Notes:
## jpeg - inverse relationship (size, download time?)

# Signals and Stories.

require('ggplot2')
require('hash')
library(gridExtra)

increment <- function(x) {
  eval.parent(substitute(x <- x + 1))
}

data = read.csv('~/data.log', header=T, sep=',')

fullMediaTypes = c(
"application/x-fcs"="application/x-fcs",
"text/json;charset=utf-8"="text/json",
"text/JavaScript"="text/javascript",
"application/x-woff"="application/x-woff",
"application/x-javascript"="application/x-javascript",
"image/jpeg"="image/jpeg",
"text/javascript; charset: UTF-8"="text/javascript",
"text/css;charset=UTF-8"="text/css",
"binary/octet-stream"="binary/octet-stream",
"image/x-icon"="image/x-icon",
"image/svg+xml"="image/svg+xml",
"application/x-shockwave-flash"="application/x-shockwave-flash",
"application/xml;charset=utf-8"="application/xml",
"text/html;charset=UTF-8"="text/html",
"text/xml;charset=utf-8"="text/xml",
"application/x-x509-ca-cert"="application/x-x",
"application/x-javascript;charset=UTF-8"="application/x-javascript",
"image/png;charset=binary"="image/png",
"text/css;charset=ISO-8859-1"="text/css",
"text/x-cross-domain-policy"="text/x-cross-domain-policy",
"text/html;;charset=iso-8859-1"="text/html",
"image/jpeg;charset=ISO-8859-1"="image/jpeg",
"image/GIF"="image/gif",
"text/css"="text/css",
"image/jpeg;charset=binary"="image/jpeg",
"text/css;charset=utf-8"="text/css",
"text/html"="text/html",
"image/gif;charset=ISO-8859-1"="image/gif",
"text/plain;charset=UTF-8"="text/plain",
"content/unknown"="content/unknown",
"image/gif;charset=UTF-8"="image/gif",
"application/json;charset=UTF-8"="application/json",
"ACK"="ACK",
"application/javascript"="application/javascript",
"application/x-javascript;charset=windows-1252"="application/x-javascript",
"text/javascript;charset=UTF-8"="text/javascript",
"text/html; Charset=utf-8"="text/html",
"image/gif"="image/gif",
"text/javascript;charset=iso-8859-1"="text/javascript",
"text/css;;charset=utf-8"="text/css",
"text/html;charset=ISO-8859-1"="text/html",
"video/x-flv"="video/x-flv",
"text/javascript"="text/javascript",
"image/png;charset=ISO-8859-1"="image/png",
"text/xml;charset=UTF-8"="text/xml",
"text/html; charset=utf-8"="text/html",
"image/jpg"="image/jpeg",
"text/html;;charset=utf-8"="text/html",
"text/javascript;charset=ISO-8859-1"="text/javascript",
"text/plain;charset=utf-8"="text/plain",
"image/gif;charset=utf-8"="image/gif",
"application/javascript;charset=ISO-8859-1"="application/javascript",
"httpd/unix-directory"="httpd/unix-directory",
"text/html;charset=us-ascii"="text/html",
"application/json;charset=ISO-8859-1"="application/json",
"application/xml"="application/xml",
"text/css; charset: UTF-8"="text/css",
"application/json;charset=utf-8"="application/json",
"application/javascript;charset=utf-8"="application/javascript",
"application/x-multiad-json;charset=UTF-8"="application/x-multiad-json",
"application/x-javascript;charset=ISO-8859-1"="application/x-javascript",
"text/xml"="text/xml",
"image/JPEG"="image/jpeg",
"text/html;charset=iso-8859-1"="text/html",
"image/vnd.microsoft.icon"="image/vnd",
"application/json"="application/json",
"text/html;ISO-8859-1;charset=ISO-8859-1"="text/html",
"image/png"="image/png",
"application/x-javascript;charset=utf-8"="application/x-javascript",
"FIN"="FIN",
"application/ocsp-response"="application/ocsp-response",
"application/javascript;charset=UTF-8"="application/javascript",
"text/plain;charset=ISO-8859-1"="text/plain",
"text/html;charset=utf-8"="text/html",
"text/xml;charset=ISO-8859-1"="text/xml",
"text/plain"="text/plain",
"application/opensearchdescription+xml"="application/opensearchdescription+xml",
"application/x-amf"="application/x-amf",
"application/octet-stream"="application/octet-stream",
"text/javascript;charset=utf-8"="text/javascript"
)

individual_plots = function(data) {
  for (pfilename in unique(data$filename)) {
    sdata = subset(data, filename == pfilename)
    q = qplot(reorder(type, rtt, min), rtt, data=sdata) +
      scale_x_discrete(name='') +
      scale_y_log10(name='RTT (log(ms))') +
      geom_boxplot() +
      opts(axis.text.x=theme_text(angle=-90, hjust=0),
           title=pfilename)
    out_svg = paste(pfilename, 'svg', sep='.')
    ggsave(out_svg)
  }
}

# individual_plots(data)

agg_plot = function(data) {
  fmedia_types = factor(data$smallLabel)

  reord = reorder(data$smallLabel, data$tcp.analysis.ack_rtt, median)  
  q = qplot(reord,
            tcp.analysis.ack_rtt, data=data, fill=cached) +
              geom_boxplot() +
              scale_x_discrete(name='') +
              scale_y_log10(name='RTT (sec)') +
              scale_fill_discrete() + 
              coord_flip()
  return(q)
}

sdata = data[data$hspa==T,]
sdata$smallLabel = fullMediaTypes[as.character(sdata$label)]
sdata$actualLength = pmax(sdata$frame.len, sdata$tcp.reassembled.length, sdata$http.content_length, na.rm=T)
cached = agg_plot(sdata)
show(cached)

p = qplot(data=sdata[sdata$smallLabel == 'image/jpeg' & sdata$cached==F,],
          actualLength, 
          tcp.analysis.ack_rtt, color=cached) + 
  scale_fill_discrete("Cached") +
  scale_x_log10() +
  scale_y_log10()

#show(p)

## flabels = sdata$label
## for (flabel in flabels) {
##   if (flabel %in% fullMediaTypes) {
##     print('YES')
##   }
## }

#View(data)
#show(q)

#qplot(length, rtt, data=data) +
#  scale_y_continuous(name='RTT (sec)', limits=c(0.03,0.2), breaks=seq(0,0.25,0.01))

## for (line in lines) {
##   sline = unsplit(strsplit(line,','))
## }

## i = 0
## frames = list()
## max_val = 0
## for (line in lines) {
##   data = unlist(strsplit(line, ','))
##   name = data[1]
##   values = as.numeric(data[2:length(data)])
##   max_val = max(max_val, values)
##   frames[[name]] = data.frame(rtts=c(values))
## }

## medians = sapply(frames, function(f) { median(f[1,]) })
## oframes = frames[order(medians)]

## plots = list()
## p = ggplot()
## for (plotname in names(oframes)) {
##   plots[[plotname]] = ggplot(oframes[[plotname]], aes(plotname,rtts)) +
##     scale_x_discrete(name='', labels=plotname) +
##     scale_y_continuous(name='RTT (sec)', limits=c(0,max_val)) +
##     geom_boxplot()
##   show(plots[[plotname]])
## }

## do.call(grid.arrange, plots)
