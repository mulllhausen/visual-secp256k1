"""
functions related to plotting and calculating points on bitcoin's elliptic curve
polynomial (secp256k1)

this file is just for understanding concepts. it should not be used for
performing live crypto operations.
"""

secp256k1_eq = "y^2 = x^3 + 7"

from distutils.version import LooseVersion
import sympy, mpmath, numpy, matplotlib, hashlib
import matplotlib.pyplot as plt

if LooseVersion(mpmath.__version__) < LooseVersion("0.19"):
	raise ImportError(
		"mpmath 0.19 or later is required. install it with `sudo python -m"
		" easy_install mpmath`"
	)

if LooseVersion(sympy.__version__) < LooseVersion("0.7.6"):
	raise ImportError(
		"sympy 0.7.6 or later is required. install it with `sudo python -m"
		" easy_install sympy`"
	)

if LooseVersion(numpy.__version__) < LooseVersion("1.6.2"):
	raise ImportError(
		"numpy 1.6.2 or later is required. install it with `sudo pip install"
		" --upgrade numpy"
	)

if LooseVersion(matplotlib.__version__) < LooseVersion("1.1.1"):
	raise ImportError(
		"matplotlib 1.1.1 or later is required. install it with `sudo apt-get"
		" install matplotlib`"
	)

def init_grunt_globals(markdown_local, md_file_local):
	"""
	initialize the globals for this module:
	markdown_local - True/False
	md_file_local - the name of the markdown file (beware - gets overwritten)
	"""
	global markdown, md_file
	(markdown, md_file) = (markdown_local, md_file_local)

################################################################################
# begin curve and line equations
################################################################################

def y_ec(xp, yp_pos):
	"""
	return either the value of y at point x = xp, or the equation for y in terms
	of xp. xp defines the scalar value of y but does not specify whether the
	result is in the top or the bottom half of the curve. the yp_pos input gives
	this:
	yp_pos == True means yp is a positive value: y = +sqrt(x^3 + 7)
	yp_pos == False means yp is a negative value: y = -sqrt(x^3 + 7)
	"""
	y = sympy.sqrt(xp**3 + 7)
	return y if yp_pos else -y

def y_line(x, p, m):
	"""
	either calculate and return the value of y at point x on the line passing
	through (xp, yp) with slope m, or return the symbolic expression for y as a
	function of x along the line:
	y = mx + c
	ie yp = m(xp) + c
	ie c = yp - m(xp)
	ie y = mx + yp - m(xp)
	ie y = m(x - xp) + yp
	"""
	(xp, yp) = p
	return m * (x - xp) + yp

def slope(p, q):
	"""
	either calculate and return the value of the slope of the line which passes
	through (xp, yp) and (xq, yq) or return the symbolic expression for this
	slope
	"""
	if p == q:
		# when both points are on top of each other then we need to find the
		# tangent slope at (xp, yp)
		return tan_slope(p)
	else:
		# p and q are two different points
		return non_tan_slope(p, q)

def tan_slope(p):
	"""
	calculate the slope of the tangent to curve y^2 = x^3 + 7 at xp.

	the curve can be written as y = sqrt(x^3 + 7) (positive and negative) and
	the slope of the tangent is the derivative:
	m = dy/dx = [+/-](0.5(x^3 + 7)^-0.5)(3x^2)
	m = [+/-]3x^2 / (2sqrt(x^3 + 7))
	m = 3x^2 / 2y
	"""
	(xp, yp) = p
	return (3 * xp**2) / (2 * yp)

def non_tan_slope(p, q):
	"""
	either calculate and return the value of the slope of the line which passes
	through (xp, yp) and (xq, yq) where p != q, or return the symbolic
	expression for this slope. the slope is the y-step over the x-step, ie
	m = (yp - yq) / (xp - xq)
	"""
	(xp, yp) = p
	(xq, yq) = q
	return (yp - yq) / (xp - xq)

def intersection(p, q):
	"""
	either calculate and return the value of the intersection coordinates of the
	line through (xp, yp) and (xq, yq) with the curve, or the symbolic
	expressions for the coordinates at this point.

	ie the intersection of line y = mx + c with curve y^2 = x^3 + 7.

	in y_line() we found y = mx + c has c = yp - m(xp) and the line and curve
	will have the same y coordinate and x coordinate at their intersections, so:

	(mx + c)^2 = x^3 + 7
	ie (mx)^2 + 2mxc + c^2 = x^3 + 7
	ie x^3 - (m^2)x^2 - 2mcx + 7 - c^2 = 0

	and we already know 2 roots of this equation (ie values of x which satisfy
	the equation) - we know that the curve and line intersect at (xp, yp) and
	at (xq, yq) :)

	the equation is order-3 so it must have 3 roots, and can be written like so:

	(x - r1)(x - r2)(x - r3) = 0
	ie (x^2 - xr2 - xr1 + r1r2)(x - r3) = 0
	ie (x^2 + (-r1 - r2)x + r1r2)(x - r3) = 0
	ie x^3 + (-r1 - r2)x^2 + xr1r2 - (r3)x^2 + (-r3)(-r1 - r2)x - r1r2r3 = 0
	ie x^3 + (-r1 - r2 - r3)x^2 + (r1r2 + r1r3 + r2r3)x - r1r2r3 = 0

	comparing terms:
	-m^2 = -r1 - r2 - r3
	and -2mc = r1r2 + r1r3 + r2r3
	and 7 - c^2 = -r1r2r3

	and since r1 = xp and r2 = xq we can just pick one of these equations to
	solve for r3. the first looks simplest:

	m^2 = r1 + r2 + r3
	ie r3 = m^2 - r1 - r2
	ie r3 = m^2 - xp - xq

	this r3 is the x coordinate of the intersection of the line with the curve.
	"""
	m = slope(p, q)
	(xp, yp) = p
	(xq, yq) = q
	r3 = m**2 - xp - xq
	return (r3, y_line(r3, p, m))
	#return (r3, y_line(r3, q, m)) # would also return the exact same thing

def tangent_intersection(p, yq_pos):
	"""
	calculate and return the value of the tangent-intersection coordinates
	(xq, yq) of the line through (xp, yp) with the curve.

	the easiest way to find the tangent point (q) of the line which passes
	through point p is to equate the two different slope equations:

	1) m = 3xq^2 / 2yq
	2) m = (yp - yq) / (xp - xq)

	(1) is the tangent slope and (2) is the non-tangent slope. we can use these
	equations to solve for xq, knowing that:

	yq = [+/-]sqrt(xq^3 + 7)

	where + or - is determined by the input variable yq_pos. note that it is a
	very difficult (impossible?) equation to solve for certain values of p, so
	we will solve numerically.

	this function works best if you pick an xp value between cuberoot(-7) and
	-0.5. for xp values outside this range you will need to adjust the numerical
	solver function - ie pick a different starting point and algorythm.
	"""
	(xp, yp) = p
	if float(xp) < -7**(1 / 3.0):
		raise ValueError("xp must be greater than cuberoot(-7)")
	xq = sympy.symbols("xq")
	yq = y_ec(xq, yq_pos)
	q = (xq, yq)
	m1 = tan_slope(q)
	m2 = non_tan_slope(p, q)
	# solve numerically, and start looking for solutions at xq = 0
	xq = float(sympy.nsolve(m1 - m2, xq, 0))
	return (xq, y_ec(xq, yq_pos))

def add_points(p, q):
	"""
	add points (xp, yp) and (xq, yq) by finding the line through them and its
	intersection with the elliptic curve (xr, yr), then mirroring point r about
	the x-axis
	"""
	r = intersection(p, q)
	(xr, yr) = r
	return (xr, -yr)

def negative(p):
	"""return the negative of point p - ie mirror it about the x-axis"""
	(xp, yp) = p
	return (xp, -yp)

def subtract_points(p, q):
	"""p - q == p + (-q)"""
	return add_points(p, negative(q))

def half_point(p, yq_pos):
	"""
	return the halving of point p. basically do the opposite of doubling - first
	mirror the point about the x-axis (-p), then compute the tangent line which 
	passes through this point and locate the tangent point (half p)
	"""
	return tangent_intersection(negative(p), yq_pos)

################################################################################
# end curve and line equations
################################################################################

################################################################################
# begin functions for plotting graphs
################################################################################

# increase this to plot a finer-grained curve - good for zooming in.
# note that this does not affect lines (which only require 2 points).
curve_steps = 10000

def init_plot_ec(x_max = 4, color = "b"):
	"""
	initialize the elliptic curve plot - create the figure and plot the curve
	but do not put any multiplication (doubling) lines on it yet and don't show
	it yet.

	we need to determine the minimum x value on the curve. y = sqrt(x^3 + 7) has
	imaginary values when (x^3 + 7) < 0, eg x = -2 -> y = sqrt(-8 + 7) = i,
	which is not a real number. so x^3 = -7, ie x = -cuberoot(7) is the minimum
	real value of x.
	"""
	global plt, x_text_offset, y_text_offset
	x_min = -(7**(1 / 3.0))

	x_text_offset = (x_max - x_min) / 20
	y_max = y_ec(x_max, yp_pos = True)
	y_min = y_ec(x_max, yp_pos = False)
	y_text_offset = (y_max - y_min) / 20

	x = sympy.symbols("x")
	y = sympy.lambdify(x, y_ec(x, yp_pos = True), "numpy")
	plt.figure() # init
	plt.grid(True)
	x_array = numpy.linspace(x_min, x_max, curve_steps)
	# the top half of the elliptic curve
	plt.plot(x_array, y(x_array), color)
	plt.plot(x_array, -y(x_array), color)
	plt.ylabel("$y$")
	plt.xlabel("$x$")
	plt.title("secp256k1: $%s$" % secp256k1_eq)

def plot_add(
	p, q, p_name, q_name, p_plus_q_name, color = "r", labels_on = True
):
	"""
	add-up two points on the curve (p & q). this involves plotting a line
	through both points and finding the third intersection with the curve (r),
	then mirroring that point about the x-axis. note that it is possible for the
	intersection to fall between p and q.

	colors:
	b: blue
	g: green
	r: red
	c: cyan
	m: magenta
	y: yellow
	k: black
	w: white

	use labels_on = False when zooming, otherwise the plot area will be expanded
	to see the text outside the zoom area
	"""
	global plt, x_text_offset, y_text_offset
	(xp, yp) = p
	(xq, yq) = q
	# first, plot the line between the two points upto the intersection with the
	# curve...

	# get the point of intersection (r)
	(xr, yr) = intersection(p, q)

	# convert sympy values into floats
	(xp, xq, xr) = (float(xp), float(xq), float(xr))
	(yp, yq, yr) = (float(yp), float(yq), float(yr))

	# get the range of values the x-axis covers
	x_min = min(xp, xq, xr)
	x_max = max(xp, xq, xr)

	# a line only needs two points
	x_array = numpy.linspace(x_min, x_max, 2)

	m = slope(p, q)
	y_array = y_line(x_array, p, m)
	plt.plot(x_array, y_array, color)

	# plot a point at p
	plt.plot(xp, yp, "%so" % color)

	if labels_on:
		# name the point at p
		p_name = ("$%s$" % p_name) if len(p_name) else ""
		plt.text(xp - x_text_offset, yp + y_text_offset, p_name)

	if p is not q:
		# plot a point at q
		plt.plot(xq, yq, "%so" % color)

		if labels_on:
			# name the point at q
			q_name = ("$%s$" % q_name) if len(q_name) else ""
			plt.text(xq - x_text_offset, yq + y_text_offset, q_name)

	# second, plot the vertical line to the other half of the curve...
	y_array = numpy.linspace(yr, -yr, 2)
	x_array = numpy.linspace(xr, xr, 2)
	plt.plot(x_array, y_array, "%s" % color)
	plt.plot(xr, -yr, "%so" % color)
	if labels_on:
		p_plus_q_name = ("$%s$" % p_plus_q_name) if len(p_plus_q_name) else ""
		plt.text(xr - x_text_offset, -yr + y_text_offset, p_plus_q_name)

def plot_subtract(
	p, q, p_name, q_name, p_minus_q_name, color = "r", labels_on = True
):
	"p - q == p + (-q)"
	plot_add(
		p, negative(q), p_name, q_name, p_minus_q_name, color, labels_on = True
	)

def finalize_plot_ec(img_filename = None):
	"""
	either display the graph as a new window or save the graph as an image and
	write a link to the image in the img dir
	"""
	##########global plt, markdown
	try:
		save = markdown
	except:
		save = False

	if save:
		plt.savefig("img/%s.png" % img_filename, bbox_inches = "tight")
		quick_write("![%s](img/%s.png)" % (img_filename, img_filename))

	else:
		plt.show(block = True)

################################################################################
# end functions for plotting graphs
################################################################################

############################################################################
# begin functions for saving/displaying math equations and text
############################################################################
def quick_write(output):
	print "%s\n" % output
	if not markdown:
		return
	with open(md_file, "a") as f:
		f.write("%s\n\n" % output)

def quick_equation(eq = None, latex = None):
	"""
	first print the given equation. optionally, in markdown mode, generate an
	image from an equation and write a link to it.
	"""
	if eq is not None:
		sympy.pprint(eq)
	else:
		print latex
	# print an empty line
	print
	if not markdown:
		return

	global plt
	if latex is None:
		latex = sympy.latex(eq)
	img_filename = hashlib.sha1(latex).hexdigest()[: 10]

	# create the figure and hide the border. set the height and width to
	# something far smaller than the resulting image - bbox_inches will
	# expand this later
	fig = plt.figure(figsize = (0.1, 0.1), frameon = False)
	ax = fig.add_axes([0, 0, 1, 1])
	ax.axis("off")
	fig = plt.gca()
	fig.axes.get_xaxis().set_visible(False)
	fig.axes.get_yaxis().set_visible(False)
	plt.text(0, 0, r"$%s$" % latex, fontsize = 25)
	plt.savefig("img/%s.png" % img_filename, bbox_inches = "tight")
	# don't use the entire latex string for the alt text as it could be long
	quick_write("![%s](img/%s.png)" % (latex[: 20], img_filename))

############################################################################
# end functions for saving/displaying math equations
############################################################################


