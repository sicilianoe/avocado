from math import ceil, floor, pow

from django.db.models import Count, Max

def distribution(queryset, field_name, datatype, exclude=[], order_by='field',
        smooth=0.01, annotate_by='id', **filters):

    """Builds a GROUP BY queryset for use as a value distribution.
    Data is binned according to a bin width specified by the
    Freedman-Diaconis Rule of h = 2 * (IQR / n^(1/3)) where
    h = bin width, IQR = Interquartile range, n = number of observations.
    Citation:
    Freedman, David; Diaconis, Persi (December 1981). "On the
    histogram as a density estimator: L2 theory" Probability
    Theory and Related Fields 57 (4): 453-476. ISSN 0178-8951.

    ``exclude`` - a list of values to be excluded from the distribution. it
    may be desired to exclude NULL values or the empty string.

    .. note::

        the default behavior of the ``exclude`` argument is to do a SQL
        equivalent of NOT IN (...). if ``None`` is included, it will have
        a custom behavior of IS NOT NULL and will be removed from the IN
        clause. default is to include all values

    ``order_by`` - specify an ordering for the distribution. the choices are
    'count', 'field', or None. default is 'count'

    ``smooth`` - smoothing facter that specifies how small a bin height can
    be compared to its neighboring bins

    ``filters`` - a dict of filters to be applied to the queryset before
    the count annotation.
    """
    name = str(field_name)

    # get base queryset
    dist = queryset

    # exclude certain values (e.g. None, '')
    if exclude:
        exclude = set(exclude)
        kwargs = {}

        # special case for null values
        if None in exclude:
            kwargs['%s__isnull' % name] = True
            exclude.remove(None)

        kwargs['%s__in' % name] = exclude
        dist = dist.exclude(**kwargs)

    # apply filters before annotation is made
    if filters:
        dist = dist.filter(**filters)

    # Apply Binning if the datatype is a number  
    if datatype == 'number' and smooth >= 0:

        # return empty list if dist is empty
        if not dist:
            return []

        # evaluate
        dist = dist.values_list(name, flat=True)
        n = dist.count()

        # raw ordered data
        dist = dist.order_by(name)

        # Bins are calculated using the Freedman-Diaconis' method.
        # F-D Method is:    h = 2 * (IQR / n^(1/3)) where
        # h = bin width, IQR is the interquartile region. 
        # Iqr = the difference in the third and first quartiles. 
        # n is the number of data points
        # This can be changed if a better method is found or could be a
        # parameter choice.
        # Citation: 
        # Freedman, David; Diaconis, Persi (December 1981). "On the
        # histogram as a density estimator: L2 theory" Probability
        # Theory and Related Fields 57 (4): 453-476. ISSN 0178-8951.

        first_quartile = 0.25
        q1_loc = int(floor(n * first_quartile))-1
        if q1_loc < 0: q1_loc = 0
        third_quartile = 0.75
        q3_loc = int(ceil(n * third_quartile))-1
        if q3_loc >= n: q3_loc = n-1

        q1 = dist[q1_loc]
        q3 = dist[q3_loc]
        iqr = q3 - q1
        h = 2 * (float(iqr) * pow(n, -(1.0 / 3.0)))
        dist = dist.annotate(count=Count(name)).values_list(name, 'count')
        minimum_pt = dist[0]
        maximum_pt = dist.reverse()[0]
        if h == 0:
            median = dist.order_by('-count')[0]
            bin_data = [(minimum_pt[0], minimum_pt[1]),
                        (median[0], median[1]),
                        (maximum_pt[0], maximum_pt[1])]
            seen = set()
            return [x for x in bin_data if x not in seen and not seen.add(x)]

        # initialize starting bin and bin height. create list for bins
        bin_data = []
        current_bin = float(minimum_pt[0]) + h
        bin_height = 0
        print h, dist
        for data_pt in dist.iterator():

            # Minimum and Max are ignored for now and will be added later
            if data_pt in [minimum_pt, maximum_pt]:
                continue

            pt = float(data_pt[0])

            # If data point is less than the current bin
            # add to the bin height
            if pt <= current_bin:
                bin_height += data_pt[1]
            if pt > current_bin:
                x = current_bin
                y = bin_height
                prev = (0, 0)
                if bin_data:
                    prev = bin_data.pop()

                # compare current bin to previous 
                # if prev bin is small, the current bin takes in previous.
                # previous bin takes in current bin, if current bin is small
                if y > 0:
                    if (y*smooth) > prev[1]:
                        fact = prev[1] / y
                        bin_x = x - (h / 2) - fact
                        bin_y = y + prev[1]
                        xy = (bin_x, bin_y)
                    elif prev[1]*smooth > y:
                        fact = y / prev[1]
                        bin_x = prev[0] + fact
                        bin_y = y + prev[1]
                        xy = (bin_x, bin_y)
                    else:
                        bin_data.append(prev)
                        bin_x = x - (h / 2)
                        xy = (bin_x, y)
                    bin_data.append(xy)

                # reset the bin height after appending bin data
                bin_height = 0

                # increment to next bin until data_pt
                # is within a bin. Add to height and 
                # move to next data_pt
                if h == 0:
                    return []
                while pt > current_bin:
                    current_bin += h

                # Once a bin is found, add in the height
                bin_height += data_pt[1]

        # Add back the min and max points and return the
        # list of X, Y coordinates.
        bin_data.insert(0, (float(minimum_pt[0]), minimum_pt[1]))
        bin_data.append((float(maximum_pt[0]), maximum_pt[1]))
        return bin_data


    # This only applies to catagorical data

    # apply annotation
    dist = dist.annotate(count=Count(annotate_by))

    # evaluate
    dist = dist.values_list(name, 'count')

    # apply ordering
    if order_by == 'count':
        dist = dist.order_by('count')
    elif order_by == 'field':
        dist = dist.order_by(name)

    return tuple(dist)

