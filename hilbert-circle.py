#!/usr/bin/python

import Image
import ImageOps
import sys, math
import sdxf

def dxf_header():
        return sdxf.Drawing()

def dxf_line(f,x1,y1,x2,y2):
        f.append(sdxf.Line(points=[(x1,y1),(x2,y2)]))

def dxf_circle(f,x,y,d):
        f.append(sdxf.Circle(center=(x,y), radius=d/2.0))

def dxf_arc(f,x,y,d,start,end):
        r = d/2.0
        f.append(sdxf.Arc(center=(x,y), radius=r, startAngle=start, endAngle=end))

def dxf_text(f,x,y,h,txt):
        f.append(sdxf.Text(txt, point=(x,y-h/2.0), height=h))

def dxf_footer(f,filename):
        f.saveas(filename)

def eq( a, b, eps=0.0001 ):
    return abs(a - b) <= eps

def normaize_angle( x1, y1, x2, y2 ):
    s1_angle = int( round( math.degrees( math.atan2( y1, x1 ) ) ) )
    s2_angle = int( round( math.degrees( math.atan2( y2, x2 ) ) ) )

    if abs( s1_angle - s2_angle ) > 90:
        if abs(s1_angle) == 180:
            s1_angle = -s1_angle
        if abs(s2_angle) == 180:
            s2_angle = -s2_angle

    return ( s1_angle, s2_angle )

# find a point that is d distance from x1,y1 and perpendicular to line x1,y1 to x2,y2
def line_perp( x1, y1, x2, y2, d ):
    (dir_x, dir_y) = line_direction( x1, y1, x2, y2 )
    #print 'dir x=%d y=%d' % (dir_x, dir_y)

    if dir_x != 0:
        d *= -1

    dx = x1 - x2
    dy = y1 - y2
    dist = math.sqrt(dx*dx + dy*dy)
    dx /= dist
    dy /= dist
    return ( x1 + d * dy, y1 + d * dx )

# find a point that is d distance from center of circle cx,cy radius r on angle a
def circle_perp( cx, cy, r, a, d ):
    return ( cx + (d + r) * -math.cos( math.radians( a ) ),
             cy + (d + r) * -math.sin( math.radians( a ) ) )

def line_direction( x1, y1, x2, y2 ):
    dx = x2 - x1
    dy = y2 - y1
    #print 'line_direction dx=%f dy=%f' % (dx, dy)
    if abs(dx) < abs(dy):
        if dy < 0:
            return (0,-1)
        else:
            return (0,1)
    else:
        if dx < 0:
            return (-1,0)
        else:
            return (1,0)

last_n=0
last_x1=0.0
last_y1=0.0
last_x2=0.0
last_y2=0.0

in1_x = 0
in1_y = 0
out1_x = 0
out1_y = 0

def draw_outline(dxf, in0_x, in0_y, out0_x, out0_y):
    global in1_x, in1_y, out1_x, out1_y

    dxf_line(dxf, in1_x, in1_y, in0_x, in0_y)
    dxf_line(dxf, out1_x, out1_y, out0_x, out0_y)

    in1_x = in0_x
    in1_y = in0_y
    out1_x = out0_x
    out1_y = out0_y

def get_img_intensity( x, y, pixels ):
    global reps, pix, pix_w, pix_h

    r = pixels / 2.0 / math.pow(2, reps)
    rMin = intensity_r * intensity_shrink
    rMax = intensity_r * (1.0 - intensity_shrink)

    img_x = int(x / pixels * pix_w)
    img_y = pix_h - int(y / pixels * pix_h)

    pixel = pix[img_x + img_y * pix_w]

    (r,g,b)=pixel

    grey = (r+g+b) / float(255*3)

    i = grey * (rMax - rMin) + rMin

    print 'pixel h=(%f,%f) img=(%d,%d) pixel=%d,%d,%d grey=%f i=%f' % (x, y, img_x, img_y, r,g,b, grey, i)

    return i

def hilbert(dxf, pixels, x0, y0, xi, xj, yi, yj, n):
    global last_n, last_x1, last_y1, last_x2, last_y2
    global in1_x, in1_y, out1_x, out1_y

    if n <= 0:
        X = x0 + (xi + yi)/2
        Y = y0 + (xj + yj)/2

        last_x0 = pixels * X
        last_y0 = pixels * Y

        print '%d (%f,%f), (%f,%f), (%f,%f)' % (last_n, last_x2, last_y2, last_x1, last_y1, last_x0, last_y0)

        if last_n == 0:
            print 'first point'
        elif last_n == 1:
            print 'second point'

            s2_x = (last_x0 - last_x1) / 2.0 + last_x1
            s2_y = (last_y0 - last_y1) / 2.0 + last_y1

            dxf_line(dxf, last_x1, last_y1, s2_x, s2_y)

            (sa_x, sa_y) = line_perp( last_x1, last_y1, s2_x, s2_y, sample_r )
            in_intesity = get_img_intensity( sa_x, sa_y, pixels )
            (in1_x, in1_y) = line_perp( last_x1, last_y1, s2_x, s2_y, in_intesity )

            (sa_x, sa_y) = line_perp( last_x1, last_y1, s2_x, s2_y, -sample_r )
            out_intesity = get_img_intensity( sa_x, sa_y, pixels )
            (out1_x, out1_y) = line_perp( last_x1, last_y1, s2_x, s2_y, -out_intesity )

            #dxf_text(dxf, last_x1, last_y1, pixels * 0.01, '%d' % (last_n) )

        else:
            s1_x = (last_x1 - last_x2) / 2.0 + last_x2
            s1_y = (last_y1 - last_y2) / 2.0 + last_y2
            s2_x = (last_x0 - last_x1) / 2.0 + last_x1
            s2_y = (last_y0 - last_y1) / 2.0 + last_y1

     	    #dxf_text(dxf, s1_x, s1_y, pixels * 0.01, '%d' % (last_n) )

            if eq(s1_x, s2_x) or eq(s1_y, s2_y):
                # straight line

                dxf_line(dxf, s1_x, s1_y, s2_x, s2_y)

                print 'straight line (%f,%f) (%f,%f)' % (s1_x, s1_y, s2_x, s2_y)

                div=5
                for i in xrange(0,div):
                    sa_x = (s2_x - s1_x) * i/float(div) + s1_x
                    sa_y = (s2_y - s1_y) * i/float(div) + s1_y

                    (in_sa_x, in_sa_y) = line_perp( sa_x, sa_y, s2_x, s2_y, sample_r )
                    in_intesity = get_img_intensity( in_sa_x, in_sa_y, pixels )
                    (in0_x, in0_y) = line_perp( sa_x, sa_y, s2_x, s2_y, in_intesity )

                    (out_sa_x, out_sa_y) = line_perp( sa_x, sa_y, s2_x, s2_y, -sample_r )
                    out_intesity = get_img_intensity( out_sa_x, out_sa_y, pixels )
                    (out0_x, out0_y) = line_perp( sa_x, sa_y, s2_x, s2_y, -out_intesity )

                    draw_outline(dxf, in0_x, in0_y, out0_x, out0_y)
		
            else:
                c_x = (last_x0 - last_x2) / 2.0 + last_x2
                c_y = (last_y0 - last_y2) / 2.0 + last_y2

                (s1_angle, s2_angle) = normaize_angle( c_x - s1_x, c_y - s1_y, c_x - s2_x, c_y - s2_y )

                if s1_angle > s2_angle:
                    in_out = -1
                else:
                    in_out = 1

                print 's1_a = %d, s2_a = %d' % (s1_angle, s2_angle)

                r_x = c_x - last_x1
                r_y = c_y - last_y1

		c_r = abs(r_x)

                div = 10
                for i in xrange(0,div):
                    a = float(i) * (s2_angle - s1_angle)/ float(div) + s1_angle

                    # find sample point
                    (sa_x, sa_y) = circle_perp( c_x, c_y, c_r, a, -sample_r )
                    in_intesity = get_img_intensity( sa_x, sa_y, pixels )

                    (sa_x, sa_y) = circle_perp( c_x, c_y, c_r, a, sample_r )
                    out_intesity = get_img_intensity( sa_x, sa_y, pixels )

                    # offset from sample point perpendicular to the circle tangent
                    (in0_x, in0_y) = circle_perp( c_x, c_y, c_r, a, in_out * -in_intesity )
                    (out0_x, out0_y) = circle_perp( c_x, c_y, c_r, a, in_out * out_intesity )
                    draw_outline(dxf, in0_x, in0_y, out0_x, out0_y)

                # for dxf output of raw curve
                if r_x > 0:
                    if r_y > 0:
                        start = 180
                        end = 270
                    else:
                        start = 90
                        end = 180
                else:
                    if r_y > 0:
                        start = 270
                        end = 360
                    else:
                        start = 0
                        end = 90

                print 'curve c=(%f,%f) r=(%f,%f)' % (c_x, c_y, r_x, r_y)
                dxf_arc(dxf, c_x, c_y, c_r * 2.0, start, end)

        # dxf output of pure hilbert
        #print '%s %s 0' % (X, Y)
        #dxf_line(dxf, last_x1, last_y1, last_x0, last_y0)
        last_n += 1
        last_x2 = last_x1
        last_y2 = last_y1
        last_x1 = last_x0
        last_y1 = last_y0
    else:
        hilbert(dxf, pixels, x0,               y0,               yi/2, yj/2, xi/2, xj/2, n - 1)
        hilbert(dxf, pixels, x0 + xi/2,        y0 + xj/2,        xi/2, xj/2, yi/2, yj/2, n - 1)
        hilbert(dxf, pixels, x0 + xi/2 + yi/2, y0 + xj/2 + yj/2, xi/2, xj/2, yi/2, yj/2, n - 1)
        hilbert(dxf, pixels, x0 + xi/2 + yi,   y0 + xj/2 + yj,  -yi/2,-yj/2,-xi/2,-xj/2, n - 1)

reps = 0

def main():
    global reps, pix, pix_w, pix_h
    global intensity_r, sample_r, intensity_shrink

    args = sys.stdin.readline()
    # Remain the loop until the renderer releases the helper...
    while args:
        arg = args.split()
        # Get the inputs
        pixels = float(arg[0])
        reps = int(arg[1])

        intensity_r = pixels / 2.0 / math.pow(2, reps)
        sample_r = intensity_r / 2.0
        intensity_shrink = 0.05

        inputFilename = arg[2]
        baseFolder = inputFilename[0:inputFilename.rfind ("/")]

        # Try to open the image using PIL, abort if not found
        print "Loading image...",
        try:
            img = Image.open(inputFilename).convert("RGB")
        except IOError:
            print "Error: input file does not exist. Aborting."
            sys.exit (1)

        (pix_w,pix_h) = img.size
        print('(original size w=%u,h=%u)' % (pix_w,pix_h))
        pix = list(img.getdata())

	dxf=dxf_header()

        # Calculate the number of curve cv's
        cvs = int(math.pow(4, reps))
            
        # Create the curve
        hilbert(dxf, pixels, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, reps)
    
        s1_x = (last_x1 - last_x2) / 2.0 + last_x2
        s1_y = (last_y1 - last_y2) / 2.0 + last_y2

        intesity = get_img_intensity( s1_x, s1_y, pixels )
        (in0_x, in0_y) = line_perp( s1_x, s1_y, last_x1, last_y1, intesity )
        (out0_x, out0_y) = line_perp( s1_x, s1_y, last_x1, last_y1, -intesity )
        draw_outline(dxf, in0_x, in0_y, out0_x, out0_y)

        # reverse in/out direction as this segment points backwards
        intesity = get_img_intensity( last_x1, last_y1, pixels )
        (in0_x, in0_y) = line_perp( last_x1, last_y1, s1_x, s1_y, -intesity )
        (out0_x, out0_y) = line_perp( last_x1, last_y1, s1_x, s1_y, intesity )
        draw_outline(dxf, in0_x, in0_y, out0_x, out0_y)

        dxf_line(dxf, s1_x, s1_y, last_x1, last_y1)

	dxf_footer(dxf,"hilbert.dxf")
        
        # read the next set of inputs
        args = sys.stdin.readline()
if __name__ == "__main__":
    main()

