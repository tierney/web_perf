# Notes:
## jpeg - inverse relationship (size, download time?)

require('ggplot2')
library(gridExtra)

increment <- function(x) {
  eval.parent(substitute(x <- x + 1))
}

lines = readLines('~/data.log')
i = 0
frames = list()
max_val = 0
for (line in lines) {
  data = unlist(strsplit(line, ','))
  name = data[1]
  values = as.numeric(data[2:length(data)])
  max_val = max(max_val, values)
  frames[[name]] = data.frame(rtts=c(values))
}

#print(frames[['application/javascript']]$rtts)
for (name in names(frames)) {
  print(frames[[name]]$rtts)
}

plots = list()
p = ggplot()
for (plotname in names(frames)) {
  plots[[plotname]] = ggplot(frames[[plotname]], aes(factor(plotname),rtts)) + 
    scale_x_discrete(name=plotname) +
    scale_y_continuous(limits=c(0,.4)) +
    geom_boxplot()
  show(plots[[plotname]])
}

do.call(grid.arrange, plots)
